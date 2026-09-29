
import os
import json
import numpy as np
import pandas as pd

from federated.client import FederatedClient
from federated.server import FederatedServer

from backend.database.database import SessionLocal
from backend.models.database_models import FederatedRound


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
    )
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "synthetic_phc_data.csv",
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "ml",
    "models",
)

GLOBAL_MODEL_PATH = os.path.join(
    MODEL_DIR,
    "federated_global_model.npz",
)

METRICS_PATH = os.path.join(
    MODEL_DIR,
    "federated_metrics.json",
)


# ============================================================
# CONFIGURATION
# ============================================================

NUM_ROUNDS = 8
LOCAL_EPOCHS = 80
LEARNING_RATE = 0.01

RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)


# ============================================================
# DATABASE
# ============================================================

def save_round_to_database(
    round_number,
    participating_phcs,
    samples,
    global_mse,
    global_rmse,
):
    db = SessionLocal()

    try:
        existing_round = (
            db.query(FederatedRound)
            .filter(
                FederatedRound.round_number
                == round_number
            )
            .first()
        )

        if existing_round:

            existing_round.participating_phcs = (
                participating_phcs
            )

            existing_round.samples = samples

            existing_round.global_mse = (
                global_mse
            )

            existing_round.global_rmse = (
                global_rmse
            )

            existing_round.algorithm = "FedAvg"

        else:

            new_round = FederatedRound(
                round_number=round_number,
                participating_phcs=participating_phcs,
                samples=samples,
                global_mse=global_mse,
                global_rmse=global_rmse,
                algorithm="FedAvg",
            )

            db.add(new_round)

        db.commit()

        print(
            f"  ✓ Round {round_number} "
            f"saved to PostgreSQL"
        )

    except Exception as error:

        db.rollback()

        print(
            f"  ✗ Database error: {error}"
        )

        raise

    finally:
        db.close()


# ============================================================
# LOAD DATA
# ============================================================

def load_dataset():

    if not os.path.exists(DATA_PATH):

        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(
        DATA_PATH
    )

    required_columns = [
        "date",
        "phc_id",
        "medicine_id",
        "medicine_name",
        "stock_quantity",
        "daily_demand",
        "received_quantity",
        "expired_quantity",
        "population",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Dataset is missing columns: "
            + ", ".join(missing)
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    if df["date"].isna().any():

        raise ValueError(
            "Dataset contains invalid dates."
        )

    numeric_columns = [
        "stock_quantity",
        "daily_demand",
        "received_quantity",
        "expired_quantity",
        "population",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    if df[numeric_columns].isna().any().any():

        raise ValueError(
            "Dataset contains invalid numeric values."
        )

    df = df.sort_values(
        [
            "phc_id",
            "medicine_id",
            "date",
        ]
    ).reset_index(
        drop=True
    )

    return df


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def build_features(df):
    """
    Build forecasting features independently for every
    PHC + medicine time series.

    Historical demand is calculated only from previous
    observations, preventing future-demand leakage.
    """

    data = df.copy()

    # --------------------------------------------------------
    # Calendar features
    # --------------------------------------------------------

    data["day_of_week"] = (
        data["date"].dt.dayofweek
    )

    data["day_of_month"] = (
        data["date"].dt.day
    )

    data["month"] = (
        data["date"].dt.month
    )

    data["day_of_year"] = (
        data["date"].dt.dayofyear
    )

    # Cyclical calendar representation
    data["dow_sin"] = np.sin(
        2
        * np.pi
        * data["day_of_week"]
        / 7.0
    )

    data["dow_cos"] = np.cos(
        2
        * np.pi
        * data["day_of_week"]
        / 7.0
    )

    data["month_sin"] = np.sin(
        2
        * np.pi
        * data["month"]
        / 12.0
    )

    data["month_cos"] = np.cos(
        2
        * np.pi
        * data["month"]
        / 12.0
    )

    # --------------------------------------------------------
    # Historical demand features
    # --------------------------------------------------------

    grouped = data.groupby(
        [
            "phc_id",
            "medicine_id",
        ],
        group_keys=False,
    )

    data["demand_lag_1"] = (
        grouped["daily_demand"]
        .shift(1)
    )

    data["demand_lag_2"] = (
        grouped["daily_demand"]
        .shift(2)
    )

    data["demand_lag_7"] = (
        grouped["daily_demand"]
        .shift(7)
    )

    data["demand_lag_14"] = (
        grouped["daily_demand"]
        .shift(14)
    )

    # --------------------------------------------------------
    # Rolling demand statistics
    #
    # Shift first so today's demand is never included
    # in today's features.
    # --------------------------------------------------------

    data["demand_rolling_7"] = (
        grouped["daily_demand"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(
                7,
                min_periods=1,
            )
            .mean()
        )
    )

    data["demand_rolling_14"] = (
        grouped["daily_demand"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(
                14,
                min_periods=1,
            )
            .mean()
        )
    )

    data["demand_rolling_std_7"] = (
        grouped["daily_demand"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(
                7,
                min_periods=2,
            )
            .std()
        )
    )

    # --------------------------------------------------------
    # Inventory features
    # --------------------------------------------------------

    data["stock_received_ratio"] = (
        data["stock_quantity"]
        /
        (
            data["received_quantity"]
            + 1.0
        )
    )

    data["expired_ratio"] = (
        data["expired_quantity"]
        /
        (
            data["stock_quantity"]
            + data["expired_quantity"]
            + 1.0
        )
    )

    # --------------------------------------------------------
    # Remove rows without enough history
    #
    # We need 14 previous observations for the strongest
    # historical feature set.
    # --------------------------------------------------------

    data = data.dropna(
        subset=[
            "demand_lag_14",
            "demand_rolling_14",
        ]
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # Replace remaining numerical issues
    # --------------------------------------------------------

    data = data.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    data = data.dropna(
        subset=[
            "demand_lag_1",
            "demand_lag_2",
            "demand_lag_7",
            "demand_lag_14",
            "demand_rolling_7",
            "demand_rolling_14",
            "demand_rolling_std_7",
        ]
    ).reset_index(
        drop=True
    )

    return data


# ============================================================
# FEATURE LIST
# ============================================================

FEATURE_COLUMNS = [

    # Inventory
    "stock_quantity",
    "received_quantity",
    "expired_quantity",
    "population",

    # Historical demand
    "demand_lag_1",
    "demand_lag_2",
    "demand_lag_7",
    "demand_lag_14",

    "demand_rolling_7",
    "demand_rolling_14",
    "demand_rolling_std_7",

    # Calendar
    "day_of_week",
    "day_of_month",
    "month",
    "day_of_year",

    "dow_sin",
    "dow_cos",
    "month_sin",
    "month_cos",

    # Inventory behavior
    "stock_received_ratio",
    "expired_ratio",
]


# ============================================================
# PREPARE FEATURES
# ============================================================

def prepare_features(df):

    X = df[
        FEATURE_COLUMNS
    ].astype(
        np.float64
    )

    y = df[
        "daily_demand"
    ].astype(
        np.float64
    )

    return X, y


# ============================================================
# CHRONOLOGICAL VALIDATION SPLIT
# ============================================================

def create_validation_split(df):

    """
    Keep the latest 15% of each PHC + medicine series
    for validation.

    This is chronological rather than random.
    """

    train_parts = []
    validation_parts = []

    for (
        phc_id,
        medicine_id,
    ), group in df.groupby(
        [
            "phc_id",
            "medicine_id",
        ]
    ):

        group = group.sort_values(
            "date"
        ).reset_index(
            drop=True
        )

        split_index = int(
            len(group) * 0.85
        )

        # Make sure both sets contain data.
        split_index = max(
            1,
            min(
                split_index,
                len(group) - 1,
            ),
        )

        train_parts.append(
            group.iloc[
                :split_index
            ]
        )

        validation_parts.append(
            group.iloc[
                split_index:
            ]
        )

    train_df = pd.concat(
        train_parts,
        ignore_index=True,
    )

    validation_df = pd.concat(
        validation_parts,
        ignore_index=True,
    )

    return (
        train_df,
        validation_df,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "================================================================="
    )

    print(
        "FEDERATED AI — PHC DEMAND FORECASTING"
    )

    print(
        "================================================================="
    )

    # ========================================================
    # LOAD
    # ========================================================

    df = load_dataset()

    print(
        f"Dataset loaded: {len(df)} records"
    )

    medicine_count = (
        df["medicine_id"].nunique()
    )

    phc_count = (
        df["phc_id"].nunique()
    )

    print(
        f"Medicines detected: {medicine_count}"
    )

    print(
        f"PHCs detected: {phc_count}"
    )

    # ========================================================
    # FEATURE ENGINEERING
    # ========================================================

    print()
    print(
        "Building historical demand features..."
    )

    df = build_features(
        df
    )

    print(
        f"Usable forecasting records: {len(df)}"
    )

    print(
        f"Features: {len(FEATURE_COLUMNS)}"
    )

    # ========================================================
    # CHRONOLOGICAL TRAIN / VALIDATION SPLIT
    # ========================================================

    train_df, validation_df = (
        create_validation_split(df)
    )

    print()
    print(
        f"Training records   : {len(train_df)}"
    )

    print(
        f"Validation records : {len(validation_df)}"
    )

    # ========================================================
    # GLOBAL TRAINING FEATURES
    # ========================================================

    X_train, y_train = (
        prepare_features(
            train_df
        )
    )

    X_validation, y_validation = (
        prepare_features(
            validation_df
        )
    )

    # ========================================================
    # GLOBAL NORMALIZATION
    # ========================================================

    feature_mean = (
        X_train.mean()
    )

    feature_std = (
        X_train.std()
    )

    feature_std = (
        feature_std.replace(
            0,
            1.0,
        )
    )

    X_train_normalized = (
        X_train
        - feature_mean
    ) / feature_std

    X_validation_normalized = (
        X_validation
        - feature_mean
    ) / feature_std

    X_train_normalized = (
        X_train_normalized
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .fillna(0.0)
    )

    X_validation_normalized = (
        X_validation_normalized
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .fillna(0.0)
    )

    # ========================================================
    # CREATE PHC CLIENTS
    # ========================================================

    clients = []

    for phc_id, phc_data in (
        train_df.groupby(
            "phc_id"
        )
    ):

        print()
        print(
            f"Preparing client: {phc_id}"
        )

        print(
            f"  Local records: "
            f"{len(phc_data)}"
        )

        X_local, y_local = (
            prepare_features(
                phc_data
            )
        )

        X_local = (
            X_local
            - feature_mean
        ) / feature_std

        X_local = (
            X_local
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
            .fillna(0.0)
        )

        client = FederatedClient(
            phc_id,
            X_local.values,
            y_local.values,
        )

        clients.append(
            client
        )

    # ========================================================
    # SERVER
    # ========================================================

    server = FederatedServer()

    server.initialize(
        feature_count=
        X_train_normalized.shape[1]
    )

    print()
    print(
        "Global model parameters: "
        f"{len(server.global_parameters)}"
    )

    print(
        f"Feature parameters: "
        f"{len(FEATURE_COLUMNS)}"
    )

    print(
        "Bias parameter: 1"
    )

    # ========================================================
    # TRAINING
    # ========================================================

    round_metrics = []

    total_samples = len(
        train_df
    )

    # ========================================================
    # FEDERATED ROUNDS
    # ========================================================

    for round_number in range(
        1,
        NUM_ROUNDS + 1,
    ):

        print()
        print(
            "-----------------------------------------------------------------"
        )

        print(
            f"FEDERATED ROUND "
            f"{round_number}/{NUM_ROUNDS}"
        )

        print(
            "-----------------------------------------------------------------"
        )

        global_parameters = (
            server.distribute()
        )

        client_parameters = []

        client_sizes = []

        # ----------------------------------------------------
        # LOCAL TRAINING
        # ----------------------------------------------------

        for client in clients:

            client.set_parameters(
                global_parameters
            )

            trained_parameters = (
                client.train(
                    epochs=LOCAL_EPOCHS,
                    learning_rate=LEARNING_RATE,
                )
            )

            if not np.all(
                np.isfinite(
                    trained_parameters
                )
            ):

                raise RuntimeError(
                    f"{client.phc_id}: "
                    "non-finite model parameters."
                )

            predictions = (
                client.predict()
            )

            predictions = np.maximum(
                predictions,
                0.0,
            )

            error = (
                predictions
                - client.y
            )

            local_mse = float(
                np.mean(
                    np.square(
                        error
                    )
                )
            )

            print(
                f"{client.phc_id}: "
                f"{client.get_sample_count()} "
                f"records | "
                f"MSE={local_mse:.4f}"
            )

            client_parameters.append(
                trained_parameters
            )

            client_sizes.append(
                client.get_sample_count()
            )

        # ----------------------------------------------------
        # FEDAVG
        # ----------------------------------------------------

        global_parameters = (
            server.aggregate(
                client_parameters,
                client_sizes,
            )
        )

        # ----------------------------------------------------
        # GLOBAL TRAINING METRIC
        # ----------------------------------------------------

        global_weights = (
            global_parameters[:-1]
        )

        global_bias = float(
            global_parameters[-1]
        )

        global_predictions = (
            X_train_normalized.values
            @ global_weights
            + global_bias
        )

        global_predictions = np.maximum(
            global_predictions,
            0.0,
        )

        global_error = (
            global_predictions
            - y_train.values
        )

        global_mse = float(
            np.mean(
                np.square(
                    global_error
                )
            )
        )

        global_rmse = float(
            np.sqrt(
                global_mse
            )
        )

        print()
        print(
            f"Global training MSE: "
            f"{global_mse:.4f}"
        )

        print(
            f"Global training RMSE: "
            f"{global_rmse:.4f}"
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        validation_predictions = (
            X_validation_normalized.values
            @ global_weights
            + global_bias
        )

        validation_predictions = np.maximum(
            validation_predictions,
            0.0,
        )

        validation_error = (
            validation_predictions
            - y_validation.values
        )

        validation_mse = float(
            np.mean(
                np.square(
                    validation_error
                )
            )
        )

        validation_rmse = float(
            np.sqrt(
                validation_mse
            )
        )

        validation_mae = float(
            np.mean(
                np.abs(
                    validation_error
                )
            )
        )

        print(
            f"Validation MSE: "
            f"{validation_mse:.4f}"
        )

        print(
            f"Validation RMSE: "
            f"{validation_rmse:.4f}"
        )

        print(
            f"Validation MAE: "
            f"{validation_mae:.4f}"
        )

        # ----------------------------------------------------
        # METRICS
        # ----------------------------------------------------

        round_metrics.append(
            {
                "round": round_number,
                "participating_phcs": len(
                    clients
                ),
                "samples": total_samples,
                "global_mse": global_mse,
                "global_rmse": global_rmse,
                "validation_mse": validation_mse,
                "validation_rmse": validation_rmse,
                "validation_mae": validation_mae,
            }
        )

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        save_round_to_database(
            round_number=round_number,
            participating_phcs=len(
                clients
            ),
            samples=total_samples,
            global_mse=global_mse,
            global_rmse=global_rmse,
        )

    # ========================================================
    # FINAL MODEL
    # ========================================================

    os.makedirs(
        MODEL_DIR,
        exist_ok=True,
    )

    np.savez(
        GLOBAL_MODEL_PATH,

        weights=global_parameters[:-1],

        bias=np.array(
            global_parameters[-1]
        ),

        parameters=global_parameters,

        feature_mean=
        feature_mean.values,

        feature_std=
        feature_std.values,

        feature_names=np.array(
            FEATURE_COLUMNS
        ),

        model_version=np.array(
            "v2.0"
        ),
    )

    # ========================================================
    # FINAL METRICS
    # ========================================================

    final_metrics = (
        round_metrics[-1]
    )

    metrics = {

        "algorithm": "FedAvg",

        "model_version": "v2.0",

        "model_type":
        "federated_historical_demand_regression",

        "participating_phcs":
        len(clients),

        "rounds":
        NUM_ROUNDS,

        "total_samples":
        total_samples,

        "medicine_count":
        medicine_count,

        "feature_count":
        len(FEATURE_COLUMNS),

        "parameter_count":
        len(global_parameters),

        "local_epochs":
        LOCAL_EPOCHS,

        "learning_rate":
        LEARNING_RATE,

        "normalization":
        "global_standardization",

        "feature_names":
        FEATURE_COLUMNS,

        "training_samples":
        len(train_df),

        "validation_samples":
        len(validation_df),

        "final_validation_rmse":
        final_metrics[
            "validation_rmse"
        ],

        "final_validation_mae":
        final_metrics[
            "validation_mae"
        ],

        "round_metrics":
        round_metrics,
    }

    with open(
        METRICS_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metrics,
            file,
            indent=4,
        )

    # ========================================================
    # COMPLETE
    # ========================================================

    print()
    print(
        "================================================================="
    )

    print(
        "FEDERATED TRAINING COMPLETE"
    )

    print(
        "================================================================="
    )

    print(
        f"PHCs participating : "
        f"{len(clients)}"
    )

    print(
        f"Training rounds    : "
        f"{NUM_ROUNDS}"
    )

    print(
        f"Training records   : "
        f"{len(train_df)}"
    )

    print(
        f"Validation records : "
        f"{len(validation_df)}"
    )

    print(
        f"Features           : "
        f"{len(FEATURE_COLUMNS)}"
    )

    print(
        f"Total parameters   : "
        f"{len(global_parameters)}"
    )

    print(
        f"Final validation RMSE : "
        f"{final_metrics['validation_rmse']:.4f}"
    )

    print(
        f"Final validation MAE  : "
        f"{final_metrics['validation_mae']:.4f}"
    )

    print(
        f"Global model saved : "
        f"{GLOBAL_MODEL_PATH}"
    )

    print(
        f"Metrics saved      : "
        f"{METRICS_PATH}"
    )

    print(
        "PostgreSQL status  : "
        f"{NUM_ROUNDS} federated rounds persisted"
    )

    print(
        "================================================================="
    )


if __name__ == "__main__":
    main()
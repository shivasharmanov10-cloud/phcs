
import os
import numpy as np


# ============================================================
# MODEL PATH
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml",
    "models",
    "federated_global_model.npz",
)


class FederatedDemandPredictor:
    """
    Production prediction service for the federated
    PHC medicine-demand forecasting model.

    The trained model uses 21 features:

        Inventory:
            stock_quantity
            received_quantity
            expired_quantity
            population

        Historical demand:
            demand_lag_1
            demand_lag_2
            demand_lag_7
            demand_lag_14
            demand_rolling_7
            demand_rolling_14
            demand_rolling_std_7

        Calendar:
            day_of_week
            day_of_month
            month
            day_of_year
            dow_sin
            dow_cos
            month_sin
            month_cos

        Inventory ratios:
            stock_received_ratio
            expired_ratio

    The model also contains a bias term.
    """

    def __init__(self, model_path=MODEL_PATH):

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Federated model not found: {model_path}"
            )

        model = np.load(
            model_path,
            allow_pickle=False,
        )

        required_keys = [
            "weights",
            "bias",
            "feature_mean",
            "feature_std",
            "feature_names",
        ]

        missing_keys = [
            key
            for key in required_keys
            if key not in model.files
        ]

        if missing_keys:
            raise ValueError(
                "Federated model is missing: "
                + ", ".join(missing_keys)
            )

        self.weights = np.asarray(
            model["weights"],
            dtype=np.float64,
        )

        self.bias = float(
            np.asarray(
                model["bias"],
                dtype=np.float64,
            )
        )

        self.feature_mean = np.asarray(
            model["feature_mean"],
            dtype=np.float64,
        )

        self.feature_std = np.asarray(
            model["feature_std"],
            dtype=np.float64,
        )

        self.feature_names = [
            str(x)
            for x in model["feature_names"]
        ]

        # ----------------------------------------------------
        # Validate dimensions
        # ----------------------------------------------------

        if self.weights.shape != (21,):
            raise ValueError(
                "Expected 21 model weights, "
                f"got {self.weights.shape}"
            )

        if self.feature_mean.shape != (21,):
            raise ValueError(
                "Expected 21 feature means, "
                f"got {self.feature_mean.shape}"
            )

        if self.feature_std.shape != (21,):
            raise ValueError(
                "Expected 21 feature standard deviations, "
                f"got {self.feature_std.shape}"
            )

        if len(self.feature_names) != 21:
            raise ValueError(
                "Expected 21 feature names, "
                f"got {len(self.feature_names)}"
            )

        # Protect against zero standard deviation.
        self.feature_std = np.where(
            self.feature_std == 0,
            1.0,
            self.feature_std,
        )

        # ----------------------------------------------------
        # Validate numerical values
        # ----------------------------------------------------

        model_values = np.concatenate(
            [
                self.weights,
                np.array([self.bias]),
                self.feature_mean,
                self.feature_std,
            ]
        )

        if not np.all(
            np.isfinite(model_values)
        ):
            raise ValueError(
                "Federated model contains "
                "non-finite values."
            )

    # ========================================================
    # FEATURE ENGINEERING
    # ========================================================

    def _build_features(
        self,
        stock_quantity,
        received_quantity,
        expired_quantity,
        population,
        demand_lag_1,
        demand_lag_2,
        demand_lag_7,
        demand_lag_14,
        demand_rolling_7,
        demand_rolling_14,
        demand_rolling_std_7,
        day_of_week,
        day_of_month,
        month,
        day_of_year,
    ):

        stock_quantity = float(stock_quantity)
        received_quantity = float(received_quantity)
        expired_quantity = float(expired_quantity)
        population = float(population)

        demand_lag_1 = float(demand_lag_1)
        demand_lag_2 = float(demand_lag_2)
        demand_lag_7 = float(demand_lag_7)
        demand_lag_14 = float(demand_lag_14)

        demand_rolling_7 = float(
            demand_rolling_7
        )

        demand_rolling_14 = float(
            demand_rolling_14
        )

        demand_rolling_std_7 = float(
            demand_rolling_std_7
        )

        day_of_week = float(day_of_week)
        day_of_month = float(day_of_month)
        month = float(month)
        day_of_year = float(day_of_year)

        # ----------------------------------------------------
        # Cyclic calendar features
        # ----------------------------------------------------

        dow_sin = np.sin(
            2.0 * np.pi * day_of_week / 7.0
        )

        dow_cos = np.cos(
            2.0 * np.pi * day_of_week / 7.0
        )

        month_sin = np.sin(
            2.0 * np.pi * month / 12.0
        )

        month_cos = np.cos(
            2.0 * np.pi * month / 12.0
        )

        # ----------------------------------------------------
        # Inventory ratios
        # ----------------------------------------------------

        stock_received_ratio = (
            stock_quantity
            / max(received_quantity, 1.0)
        )

        expired_ratio = (
            expired_quantity
            / max(
                stock_quantity + received_quantity,
                1.0,
            )
        )

        features = np.array(
            [
                stock_quantity,
                received_quantity,
                expired_quantity,
                population,

                demand_lag_1,
                demand_lag_2,
                demand_lag_7,
                demand_lag_14,

                demand_rolling_7,
                demand_rolling_14,
                demand_rolling_std_7,

                day_of_week,
                day_of_month,
                month,
                day_of_year,

                dow_sin,
                dow_cos,
                month_sin,
                month_cos,

                stock_received_ratio,
                expired_ratio,
            ],
            dtype=np.float64,
        )

        if not np.all(
            np.isfinite(features)
        ):
            raise ValueError(
                "Generated features contain "
                "invalid values."
            )

        return features

    # ========================================================
    # NORMALIZATION
    # ========================================================

    def _normalize(self, features):

        normalized = (
            features - self.feature_mean
        ) / self.feature_std

        if not np.all(
            np.isfinite(normalized)
        ):
            raise ValueError(
                "Feature normalization produced "
                "invalid values."
            )

        return normalized

    # ========================================================
    # PREDICTION
    # ========================================================

    def predict(
        self,
        stock_quantity,
        received_quantity,
        expired_quantity,
        population,
        demand_lag_1,
        demand_lag_2,
        demand_lag_7,
        demand_lag_14,
        demand_rolling_7,
        demand_rolling_14,
        demand_rolling_std_7,
        day_of_week,
        day_of_month,
        month,
        day_of_year,
    ):

        features = self._build_features(
            stock_quantity,
            received_quantity,
            expired_quantity,
            population,
            demand_lag_1,
            demand_lag_2,
            demand_lag_7,
            demand_lag_14,
            demand_rolling_7,
            demand_rolling_14,
            demand_rolling_std_7,
            day_of_week,
            day_of_month,
            month,
            day_of_year,
        )

        normalized = self._normalize(
            features
        )

        prediction = float(
            np.dot(
                normalized,
                self.weights,
            )
            + self.bias
        )

        # Demand cannot be negative.
        prediction = max(
            0.0,
            prediction,
        )

        return prediction

    # ========================================================
    # OPERATIONAL ANALYSIS
    # ========================================================

    def analyze(
        self,
        stock_quantity,
        received_quantity,
        expired_quantity,
        population,
        demand_lag_1,
        demand_lag_2,
        demand_lag_7,
        demand_lag_14,
        demand_rolling_7,
        demand_rolling_14,
        demand_rolling_std_7,
        day_of_week,
        day_of_month,
        month,
        day_of_year,
    ):

        predicted_demand = self.predict(
            stock_quantity,
            received_quantity,
            expired_quantity,
            population,
            demand_lag_1,
            demand_lag_2,
            demand_lag_7,
            demand_lag_14,
            demand_rolling_7,
            demand_rolling_14,
            demand_rolling_std_7,
            day_of_week,
            day_of_month,
            month,
            day_of_year,
        )

        stock = float(
            stock_quantity
        )

        # ----------------------------------------------------
        # STOCK COVERAGE
        # ----------------------------------------------------

        if predicted_demand > 0:

            stock_days = (
                stock / predicted_demand
            )

        else:

            stock_days = float("inf")

        # ----------------------------------------------------
        # RISK
        # ----------------------------------------------------

        if stock_days < 3:

            risk = "critical"

        elif stock_days < 7:

            risk = "high"

        elif stock_days < 14:

            risk = "moderate"

        else:

            risk = "low"

        # ----------------------------------------------------
        # 14-DAY STOCK REQUIREMENT
        # ----------------------------------------------------

        recommended_stock = (
            predicted_demand * 14
        )

        shortage_quantity = max(
            0.0,
            recommended_stock - stock,
        )

        surplus_quantity = max(
            0.0,
            stock - recommended_stock,
        )

        recommended_order = (
            shortage_quantity
        )

        # ----------------------------------------------------
        # EXPIRED STOCK RATIO
        # ----------------------------------------------------

        total_stock_received = (
            stock
            + float(received_quantity)
        )

        if total_stock_received > 0:

            expired_ratio_percent = (
                float(expired_quantity)
                / total_stock_received
            ) * 100.0

        else:

            expired_ratio_percent = 0.0

        return {
            "predicted_daily_demand": round(
                predicted_demand,
                2,
            ),

            "current_stock": int(
                stock_quantity
            ),

            "estimated_stock_days": (
                round(
                    stock_days,
                    2,
                )
                if np.isfinite(stock_days)
                else None
            ),

            "risk_level": risk,

            "recommended_14_day_stock": round(
                recommended_stock,
                2,
            ),

            "shortage_quantity": round(
                shortage_quantity,
                2,
            ),

            "surplus_quantity": round(
                surplus_quantity,
                2,
            ),

            "recommended_order_quantity": round(
                recommended_order,
                2,
            ),

            "expired_stock_ratio_percent": round(
                expired_ratio_percent,
                2,
            ),
        }


# ============================================================
# SHARED MODEL INSTANCE
# ============================================================

predictor = FederatedDemandPredictor()

from pathlib import Path
from uuid import uuid4

import pandas as pd

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.database_models import (
    AIDecisionAudit,
    PHC,
    Medicine,
)
from ml.federated_predictor import predictor


router = APIRouter(
    prefix="/api/ml",
    tags=["Machine Learning"],
)


MODEL_DIR = Path("ml/models")


# ============================================================
# LIVE FEDERATED PREDICTION REQUEST
# ============================================================

class DemandPredictionRequest(BaseModel):

    # --------------------------------------------------------
    # REAL PHC / MEDICINE IDENTITY
    # --------------------------------------------------------

    phc_id: str = Field(
        min_length=1,
        max_length=50,
    )

    medicine_id: str = Field(
        min_length=1,
        max_length=50,
    )

    # --------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------

    stock_quantity: float = Field(
        ge=0
    )

    received_quantity: float = Field(
        ge=0
    )

    expired_quantity: float = Field(
        ge=0
    )

    population: float = Field(
        gt=0
    )

    # --------------------------------------------------------
    # DEMAND FEATURES
    # --------------------------------------------------------

    demand_lag_1: float = Field(
        ge=0
    )

    demand_lag_2: float = Field(
        ge=0
    )

    demand_lag_7: float = Field(
        ge=0
    )

    demand_lag_14: float = Field(
        ge=0
    )

    demand_rolling_7: float = Field(
        ge=0
    )

    demand_rolling_14: float = Field(
        ge=0
    )

    demand_rolling_std_7: float = Field(
        ge=0
    )

    # --------------------------------------------------------
    # CALENDAR FEATURES
    # --------------------------------------------------------

    day_of_week: int = Field(
        ge=0,
        le=6,
    )

    day_of_month: int = Field(
        ge=1,
        le=31,
    )

    month: int = Field(
        ge=1,
        le=12,
    )

    day_of_year: int = Field(
        ge=1,
        le=366,
    )


# ============================================================
# HELPER
# ============================================================

def load_csv(filename: str):

    path = MODEL_DIR / filename

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail=f"ML output not found: {filename}",
        )

    return pd.read_csv(path)


# ============================================================
# SAFE NUMBER CONVERSION
# ============================================================

def safe_float(
    value,
    default=0.0,
):

    try:

        if value is None:
            return default

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return default


# ============================================================
# LIVE FEDERATED DEMAND PREDICTION
# + PHC / MEDICINE VALIDATION
# + AI DECISION AUDIT
# ============================================================

@router.post("/predict")
def predict_demand(
    request: DemandPredictionRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # REQUEST ID
    # --------------------------------------------------------

    request_id = (
        http_request.headers.get(
            "X-Request-ID"
        )
        or str(uuid4())
    )

    try:

        # ====================================================
        # 1. FIND ACTIVE PHC
        # ====================================================

        phc = (
            db.query(PHC)
            .filter(
                PHC.phc_id == request.phc_id,
                PHC.active.is_(True),
            )
            .first()
        )

        if not phc:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Active PHC not found: "
                    f"{request.phc_id}"
                ),
            )

        # ====================================================
        # 2. FIND MEDICINE
        # ====================================================

        medicine = (
            db.query(Medicine)
            .filter(
                Medicine.medicine_id
                == request.medicine_id
            )
            .first()
        )

        if not medicine:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Medicine not found: "
                    f"{request.medicine_id}"
                ),
            )

        # ====================================================
        # 3. RUN EXISTING FEDERATED ML MODEL
        # ====================================================

        result = predictor.analyze(

            stock_quantity=request.stock_quantity,

            received_quantity=(
                request.received_quantity
            ),

            expired_quantity=(
                request.expired_quantity
            ),

            population=request.population,

            demand_lag_1=(
                request.demand_lag_1
            ),

            demand_lag_2=(
                request.demand_lag_2
            ),

            demand_lag_7=(
                request.demand_lag_7
            ),

            demand_lag_14=(
                request.demand_lag_14
            ),

            demand_rolling_7=(
                request.demand_rolling_7
            ),

            demand_rolling_14=(
                request.demand_rolling_14
            ),

            demand_rolling_std_7=(
                request.demand_rolling_std_7
            ),

            day_of_week=(
                request.day_of_week
            ),

            day_of_month=(
                request.day_of_month
            ),

            month=request.month,

            day_of_year=(
                request.day_of_year
            ),
        )

        # ====================================================
        # 4. MODEL METADATA
        # ====================================================

        model_name = (
            "Federated PHC Demand Forecasting"
        )

        model_version = getattr(
            predictor,
            "model_version",
            "federated-global",
        )

        # ====================================================
        # 5. EXTRACT AI DECISION VALUES
        # ====================================================

        predicted_daily_demand = safe_float(
            result.get(
                "predicted_daily_demand"
            )
        )

        current_stock = safe_float(
            result.get(
                "current_stock",
                request.stock_quantity,
            )
        )

        estimated_stock_days = safe_float(
            result.get(
                "estimated_stock_days"
            )
        )

        risk_level = result.get(
            "risk_level"
        )

        recommended_order_quantity = safe_float(
            result.get(
                "recommended_order_quantity"
            )
        )

        shortage_quantity = safe_float(
            result.get(
                "shortage_quantity"
            )
        )

        surplus_quantity = safe_float(
            result.get(
                "surplus_quantity"
            )
        )

        expired_stock_ratio_percent = safe_float(
            result.get(
                "expired_stock_ratio_percent"
            )
        )

        # ====================================================
        # 6. CREATE AI DECISION AUDIT
        # ====================================================

        audit = AIDecisionAudit(

            request_id=request_id,

            phc_id=phc.phc_id,

            medicine_id=medicine.medicine_id,

            medicine_name=medicine.name,

            decision_type=(
                "federated_demand_prediction"
            ),

            model_name=model_name,

            model_version=model_version,

            predicted_daily_demand=(
                predicted_daily_demand
            ),

            current_stock=current_stock,

            estimated_stock_days=(
                estimated_stock_days
            ),

            risk_level=risk_level,

            recommended_order_quantity=(
                recommended_order_quantity
            ),

            shortage_quantity=(
                shortage_quantity
            ),

            surplus_quantity=(
                surplus_quantity
            ),

            expired_stock_ratio_percent=(
                expired_stock_ratio_percent
            ),
        )

        db.add(audit)

        db.commit()

        db.refresh(audit)

        # ====================================================
        # 7. RETURN COMPLETE AI DECISION
        # ====================================================

        return {

            "success": True,

            "request_id": request_id,

            "audit_id": audit.id,

            "phc": {

                "id": phc.phc_id,

                "name": phc.name,

                "district": phc.district,

                "population": phc.population,

                "active": phc.active,

            },

            "medicine": {

                "id": medicine.medicine_id,

                "name": medicine.name,

                "category": medicine.category,

                "unit": medicine.unit,

                "minimum_stock": (
                    medicine.minimum_stock
                ),

            },

            "model": model_name,

            "model_version": model_version,

            "prediction": result,
        }

    # ========================================================
    # VALIDATION / HTTP ERROR
    # ========================================================

    except HTTPException:

        db.rollback()

        raise

    # ========================================================
    # MODEL VALUE ERROR
    # ========================================================

    except ValueError as error:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    # ========================================================
    # UNEXPECTED ERROR
    # ========================================================

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Prediction failed: {error}"
            ),
        )


# ============================================================
# STOCK RISK
# ============================================================

@router.get("/stock-risk")
def get_stock_risk():

    df = load_csv(
        "stock_risk_report.csv"
    )

    return {

        "count": len(df),

        "data": df.fillna("").to_dict(
            orient="records"
        ),

    }


# ============================================================
# ANOMALIES
# ============================================================

@router.get("/anomalies")
def get_anomalies():

    df = load_csv(
        "anomaly_report.csv"
    )

    if "date" in df.columns:

        df = df.sort_values(
            "date",
            ascending=False,
        )

    return {

        "count": len(df),

        "data": df.fillna("").to_dict(
            orient="records"
        ),

    }


# ============================================================
# REDISTRIBUTION
# ============================================================

@router.get("/redistribution")
def get_redistribution():

    df = load_csv(
        "redistribution_recommendations.csv"
    )

    return {

        "count": len(df),

        "data": df.fillna("").to_dict(
            orient="records"
        ),

    }


# ============================================================
# FORECAST
# ============================================================

@router.get("/forecast")
def get_forecast():

    prediction_file = (
        MODEL_DIR
        / "demand_predictions.csv"
    )

    if not prediction_file.exists():

        return {

            "count": 0,

            "data": [],

            "message": (
                "Demand predictions will be "
                "available after the forecasting "
                "pipeline exports them."
            ),

        }

    df = pd.read_csv(
        prediction_file
    )

    return {

        "count": len(df),

        "data": df.fillna("").to_dict(
            orient="records"
        ),

    }


# ============================================================
# ML SUMMARY
# ============================================================

@router.get("/summary")
def get_ml_summary():

    stock = load_csv(
        "stock_risk_report.csv"
    )

    anomalies = load_csv(
        "anomaly_report.csv"
    )

    redistribution = load_csv(
        "redistribution_recommendations.csv"
    )

    high_risk = 0
    medium_risk = 0
    low_risk = 0

    if "risk_level" in stock.columns:

        risk_counts = (
            stock["risk_level"]
            .astype(str)
            .str.upper()
            .value_counts()
        )

        high_risk = int(
            risk_counts.get(
                "HIGH",
                0,
            )
        )

        medium_risk = int(
            risk_counts.get(
                "MEDIUM",
                0,
            )
        )

        low_risk = int(
            risk_counts.get(
                "LOW",
                0,
            )
        )

    return {

        "stock_risk": {

            "high": high_risk,

            "medium": medium_risk,

            "low": low_risk,

        },

        "anomalies": len(
            anomalies
        ),

        "redistribution_recommendations": len(
            redistribution
        ),

    }
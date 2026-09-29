
from datetime import datetime

from sqlalchemy.orm import Session

from backend.models.database_models import Alert


def create_stock_alert(
    db: Session,
    *,
    phc_id: int,
    medicine_id: int | None,
    risk_level: str,
    current_stock: float,
    predicted_daily_demand: float,
    estimated_stock_days: float,
    shortage_quantity: float,
):
    """
    Convert an ML stock-risk decision into a persistent
    operational alert.

    The ML model remains responsible for prediction.
    This service is responsible for operationalization.
    """

    risk = str(
        risk_level or "UNKNOWN"
    ).upper()

    # --------------------------------------------------------
    # Determine alert type and severity
    # --------------------------------------------------------

    if shortage_quantity > 0:

        alert_type = "STOCK_SHORTAGE"

        if risk == "HIGH":
            severity = "CRITICAL"
        elif risk == "MEDIUM":
            severity = "HIGH"
        else:
            severity = "MEDIUM"

        message = (
            f"Medicine stock shortage detected. "
            f"Current stock: {current_stock:.2f}. "
            f"Predicted daily demand: "
            f"{predicted_daily_demand:.2f}. "
            f"Estimated stock duration: "
            f"{estimated_stock_days:.2f} days. "
            f"Estimated shortage: "
            f"{shortage_quantity:.2f} units."
        )

    elif risk == "HIGH":

        alert_type = "HIGH_STOCK_RISK"
        severity = "CRITICAL"

        message = (
            f"High stock risk detected. "
            f"Current stock: {current_stock:.2f}. "
            f"Predicted daily demand: "
            f"{predicted_daily_demand:.2f}. "
            f"Estimated stock duration: "
            f"{estimated_stock_days:.2f} days."
        )

    elif risk == "MEDIUM":

        alert_type = "MEDIUM_STOCK_RISK"
        severity = "HIGH"

        message = (
            f"Medium stock risk detected. "
            f"Current stock: {current_stock:.2f}. "
            f"Predicted daily demand: "
            f"{predicted_daily_demand:.2f}. "
            f"Estimated stock duration: "
            f"{estimated_stock_days:.2f} days."
        )

    else:

        # ----------------------------------------------------
        # LOW RISK = no operational alert
        # ----------------------------------------------------

        return None

    # --------------------------------------------------------
    # Avoid creating duplicate unresolved alerts
    # --------------------------------------------------------

    existing = (
        db.query(Alert)
        .filter(
            Alert.phc_id == phc_id,
            Alert.medicine_id == medicine_id,
            Alert.alert_type == alert_type,
            Alert.resolved.is_(False),
        )
        .first()
    )

    if existing:

        return existing

    # --------------------------------------------------------
    # Persist alert
    # --------------------------------------------------------

    alert = Alert(
        phc_id=phc_id,
        medicine_id=medicine_id,
        alert_type=alert_type,
        severity=severity,
        message=message,
        resolved=False,
        created_at=datetime.utcnow(),
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert
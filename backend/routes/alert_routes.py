
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.database_models import Alert


router = APIRouter(
    prefix="/api/alerts",
    tags=["Operational Alerts"],
)


# ============================================================
# ACTIVE ALERTS
# ============================================================

@router.get("")
def get_alerts(
    db: Session = Depends(get_db),
):

    alerts = (
        db.query(Alert)
        .filter(
            Alert.resolved.is_(False)
        )
        .order_by(
            Alert.created_at.desc()
        )
        .all()
    )

    return {
        "count": len(alerts),
        "data": [
            {
                "id": alert.id,
                "phc_id": alert.phc_id,
                "medicine_id": alert.medicine_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "resolved": alert.resolved,
                "created_at": alert.created_at,
            }
            for alert in alerts
        ],
    }


# ============================================================
# RESOLVE ALERT
# ============================================================

@router.patch("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):

    alert = (
        db.query(Alert)
        .filter(
            Alert.id == alert_id
        )
        .first()
    )

    if not alert:

        raise HTTPException(
            status_code=404,
            detail="Alert not found.",
        )

    alert.resolved = True

    db.commit()
    db.refresh(alert)

    return {
        "success": True,
        "message": "Alert resolved.",
        "alert": {
            "id": alert.id,
            "phc_id": alert.phc_id,
            "medicine_id": alert.medicine_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "resolved": alert.resolved,
        },
    }
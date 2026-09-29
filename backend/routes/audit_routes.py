
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.database_models import AIDecisionAudit


router = APIRouter(
    prefix="/api/audit",
    tags=["AI Audit"],
)


@router.get("")
def get_ai_audits(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(AIDecisionAudit)
        .order_by(AIDecisionAudit.id.desc())
        .limit(limit)
        .all()
    )

    return {
        "success": True,
        "count": len(rows),
        "data": [
            {
                "id": row.id,
                "request_id": row.request_id,
                "phc_id": row.phc_id,
                "medicine_id": row.medicine_id,
                "medicine_name": row.medicine_name,
                "decision_type": row.decision_type,
                "model_name": row.model_name,
                "model_version": row.model_version,
                "predicted_daily_demand": row.predicted_daily_demand,
                "current_stock": row.current_stock,
                "estimated_stock_days": row.estimated_stock_days,
                "risk_level": row.risk_level,
                "recommended_order_quantity": (
                    row.recommended_order_quantity
                ),
                "shortage_quantity": row.shortage_quantity,
                "surplus_quantity": row.surplus_quantity,
                "expired_stock_ratio_percent": (
                    row.expired_stock_ratio_percent
                ),
                "created_at": row.created_at,
            }
            for row in rows
        ],
    }


@router.get("/summary")
def get_audit_summary(
    db: Session = Depends(get_db),
):
    total = db.query(AIDecisionAudit).count()

    high = (
        db.query(AIDecisionAudit)
        .filter(AIDecisionAudit.risk_level == "high")
        .count()
    )

    medium = (
        db.query(AIDecisionAudit)
        .filter(AIDecisionAudit.risk_level == "medium")
        .count()
    )

    low = (
        db.query(AIDecisionAudit)
        .filter(AIDecisionAudit.risk_level == "low")
        .count()
    )

    return {
        "success": True,
        "total_decisions": total,
        "risk_distribution": {
            "high": high,
            "medium": medium,
            "low": low,
        },
    }
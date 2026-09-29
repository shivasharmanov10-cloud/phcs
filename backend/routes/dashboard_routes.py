
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.database_models import (
    AIDecisionAudit,
    Inventory,
    Medicine,
    PHC,
    RedistributionRequest,
    Alert,
    FederatedRound,
)

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


@router.get("/overview")
def dashboard_overview(
    db: Session = Depends(get_db),
):
    # ---------------------------------------------------------
    # PHCs
    # ---------------------------------------------------------

    total_phcs = (
        db.query(PHC)
        .count()
    )

    active_phcs = (
        db.query(PHC)
        .filter(PHC.active.is_(True))
        .count()
    )

    # ---------------------------------------------------------
    # Medicines
    # ---------------------------------------------------------

    total_medicines = (
        db.query(Medicine)
        .count()
    )

    # ---------------------------------------------------------
    # Inventory
    # ---------------------------------------------------------

    inventory_rows = (
        db.query(Inventory)
        .all()
    )

    total_stock = sum(
        int(row.stock_quantity or 0)
        for row in inventory_rows
    )

    total_received = sum(
        int(row.received_quantity or 0)
        for row in inventory_rows
    )

    total_expired = sum(
        int(row.expired_quantity or 0)
        for row in inventory_rows
    )

    # ---------------------------------------------------------
    # AI AUDITS
    # ---------------------------------------------------------

    audits = (
        db.query(AIDecisionAudit)
        .order_by(
            AIDecisionAudit.id.desc()
        )
        .all()
    )

    high_risk = sum(
        1
        for row in audits
        if str(row.risk_level).lower() == "high"
    )

    medium_risk = sum(
        1
        for row in audits
        if str(row.risk_level).lower() == "medium"
    )

    low_risk = sum(
        1
        for row in audits
        if str(row.risk_level).lower() == "low"
    )

    # ---------------------------------------------------------
    # REDISTRIBUTION
    # ---------------------------------------------------------

    pending_redistribution = (
        db.query(RedistributionRequest)
        .filter(
            RedistributionRequest.status
            == "pending"
        )
        .count()
    )

    approved_redistribution = (
        db.query(RedistributionRequest)
        .filter(
            RedistributionRequest.status
            == "approved"
        )
        .count()
    )

    total_redistribution = (
        db.query(RedistributionRequest)
        .count()
    )

    # ---------------------------------------------------------
    # ALERTS
    # ---------------------------------------------------------

    active_alerts = (
        db.query(Alert)
        .filter(
            Alert.resolved.is_(False)
        )
        .count()
    )

    # ---------------------------------------------------------
    # FEDERATED LEARNING
    # ---------------------------------------------------------

    latest_round = (
        db.query(FederatedRound)
        .order_by(
            FederatedRound.round_number.desc()
        )
        .first()
    )

    federated = None

    if latest_round:
        federated = {
            "round_number": latest_round.round_number,
            "participating_phcs": (
                latest_round.participating_phcs
            ),
            "samples": latest_round.samples,
            "global_mse": latest_round.global_mse,
            "global_rmse": latest_round.global_rmse,
            "algorithm": latest_round.algorithm,
            "created_at": latest_round.created_at,
        }

    # ---------------------------------------------------------
    # RECENT AI DECISIONS
    # ---------------------------------------------------------

    recent_decisions = [
        {
            "id": row.id,
            "request_id": row.request_id,
            "phc_id": row.phc_id,
            "medicine_id": row.medicine_id,
            "medicine_name": row.medicine_name,
            "decision_type": row.decision_type,
            "predicted_daily_demand": (
                row.predicted_daily_demand
            ),
            "current_stock": row.current_stock,
            "estimated_stock_days": (
                row.estimated_stock_days
            ),
            "risk_level": row.risk_level,
            "recommended_order_quantity": (
                row.recommended_order_quantity
            ),
            "shortage_quantity": (
                row.shortage_quantity
            ),
            "surplus_quantity": (
                row.surplus_quantity
            ),
            "created_at": row.created_at,
        }
        for row in audits[:10]
    ]

    # ---------------------------------------------------------
    # FINAL RESPONSE
    # ---------------------------------------------------------

    return {
        "success": True,

        "system": {
            "status": "operational",
            "total_phcs": total_phcs,
            "active_phcs": active_phcs,
            "total_medicines": total_medicines,
        },

        "inventory": {
            "total_stock": total_stock,
            "total_received": total_received,
            "total_expired": total_expired,
        },

        "ai": {
            "total_decisions": len(audits),
            "risk_distribution": {
                "high": high_risk,
                "medium": medium_risk,
                "low": low_risk,
            },
        },

        "redistribution": {
            "total": total_redistribution,
            "pending": pending_redistribution,
            "approved": approved_redistribution,
        },

        "alerts": {
            "active": active_alerts,
        },

        "federated_learning": federated,

        "recent_decisions": recent_decisions,
    }
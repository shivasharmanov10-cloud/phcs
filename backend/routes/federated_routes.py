
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.database_models import FederatedRound


router = APIRouter(
    prefix="/api/federated",
    tags=["Federated AI"],
)


@router.get("/status")
def get_federated_status(
    db: Session = Depends(get_db),
):
    """
    Return the current federated-learning status
    using data stored in PostgreSQL.
    """

    rounds = (
        db.query(FederatedRound)
        .order_by(FederatedRound.round_number.asc())
        .all()
    )

    if not rounds:
        raise HTTPException(
            status_code=404,
            detail="No federated training rounds found in the database.",
        )

    latest = rounds[-1]

    total_samples = sum(
        round_data.samples
        for round_data in rounds
    )

    return {
        "status": "active",
        "algorithm": latest.algorithm,
        "participating_phcs": latest.participating_phcs,
        "training_rounds": len(rounds),
        "total_samples": total_samples,
        "latest_round": {
            "round": latest.round_number,
            "participating_phcs": latest.participating_phcs,
            "samples": latest.samples,
            "global_mse": latest.global_mse,
            "global_rmse": latest.global_rmse,
        },
        "data_policy": (
            "Raw PHC training data remains local. "
            "Only model updates and aggregate metrics are shared."
        ),
    }


@router.get("/rounds")
def get_federated_rounds(
    db: Session = Depends(get_db),
):
    """
    Return all federated-learning rounds
    stored in PostgreSQL.
    """

    rounds = (
        db.query(FederatedRound)
        .order_by(FederatedRound.round_number.asc())
        .all()
    )

    return {
        "count": len(rounds),
        "rounds": [
            {
                "round": item.round_number,
                "participating_phcs": item.participating_phcs,
                "samples": item.samples,
                "global_mse": item.global_mse,
                "global_rmse": item.global_rmse,
                "algorithm": item.algorithm,
                "created_at": (
                    item.created_at.isoformat()
                    if item.created_at
                    else None
                ),
            }
            for item in rounds
        ],
    }
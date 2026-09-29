
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.database_models import (
    Inventory,
    RedistributionRequest,
    User,
)
from backend.routes.auth_routes import (
    get_current_user,
    require_roles,
)
from backend.services.redistribution_service import (
    generate_redistribution_recommendations,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/redistribution",
    tags=["Redistribution"],
)


# ============================================================
# SCHEMAS
# ============================================================

class RedistributionRecommendationRequest(BaseModel):
    medicine_id: int = Field(gt=0)
    destination_phc_id: int = Field(gt=0)
    shortage_quantity: float = Field(gt=0)


# ============================================================
# RECOMMEND REDISTRIBUTION
# ============================================================

@router.post("/recommend")
def recommend_redistribution(
    request: RedistributionRecommendationRequest,
    db: Session = Depends(get_db),
):
    recommendations = (
        generate_redistribution_recommendations(
            db,
            medicine_id=request.medicine_id,
            destination_phc_id=request.destination_phc_id,
            shortage_quantity=request.shortage_quantity,
        )
    )

    return {
        "success": True,
        "count": len(recommendations),
        "data": [
            {
                "id": item.id,
                "medicine_id": item.medicine_id,
                "source_phc_id": item.source_phc_id,
                "destination_phc_id": item.destination_phc_id,
                "quantity": item.quantity,
                "reason": item.reason,
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in recommendations
        ],
    }


# ============================================================
# APPROVE REDISTRIBUTION
# ADMIN / DISTRICT OFFICER ONLY
# ============================================================

@router.post("/{request_id}/approve")
def approve_redistribution(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "admin",
            "district_officer",
        )
    ),
):
    redistribution = (
        db.query(RedistributionRequest)
        .filter(
            RedistributionRequest.id == request_id
        )
        .first()
    )

    if not redistribution:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Redistribution request "
                f"{request_id} not found"
            ),
        )

    # Only pending requests can be approved
    if redistribution.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Redistribution request is already "
                f"{redistribution.status}"
            ),
        )

    # --------------------------------------------------------
    # SOURCE INVENTORY
    # --------------------------------------------------------

    source_inventory = (
        db.query(Inventory)
        .filter(
            Inventory.phc_id
            == redistribution.source_phc_id,
            Inventory.medicine_id
            == redistribution.medicine_id,
        )
        .first()
    )

    if not source_inventory:
        raise HTTPException(
            status_code=404,
            detail="Source inventory not found",
        )

    # --------------------------------------------------------
    # CHECK SOURCE STOCK
    # --------------------------------------------------------

    if (
        source_inventory.stock_quantity
        < redistribution.quantity
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Insufficient source inventory. "
                f"Available: "
                f"{source_inventory.stock_quantity}, "
                f"required: "
                f"{redistribution.quantity}"
            ),
        )

    # --------------------------------------------------------
    # DESTINATION INVENTORY
    # --------------------------------------------------------

    destination_inventory = (
        db.query(Inventory)
        .filter(
            Inventory.phc_id
            == redistribution.destination_phc_id,
            Inventory.medicine_id
            == redistribution.medicine_id,
        )
        .first()
    )

    # Create destination inventory if it doesn't exist
    if not destination_inventory:
        destination_inventory = Inventory(
            phc_id=redistribution.destination_phc_id,
            medicine_id=redistribution.medicine_id,
            stock_quantity=0,
            received_quantity=0,
            expired_quantity=0,
        )

        db.add(destination_inventory)
        db.flush()

    # --------------------------------------------------------
    # TRANSFER STOCK
    # --------------------------------------------------------

    quantity = redistribution.quantity

    source_inventory.stock_quantity -= quantity

    destination_inventory.stock_quantity += quantity

    destination_inventory.received_quantity += quantity

    redistribution.status = "approved"

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    db.commit()

    db.refresh(redistribution)
    db.refresh(source_inventory)
    db.refresh(destination_inventory)

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "success": True,
        "message": "Redistribution approved successfully",

        "approved_by": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
        },

        "request": {
            "id": redistribution.id,
            "medicine_id": redistribution.medicine_id,
            "source_phc_id": (
                redistribution.source_phc_id
            ),
            "destination_phc_id": (
                redistribution.destination_phc_id
            ),
            "quantity": redistribution.quantity,
            "status": redistribution.status,
        },

        "inventory": {
            "source": {
                "phc_id": source_inventory.phc_id,
                "medicine_id": (
                    source_inventory.medicine_id
                ),
                "stock_quantity": (
                    source_inventory.stock_quantity
                ),
            },

            "destination": {
                "phc_id": (
                    destination_inventory.phc_id
                ),
                "medicine_id": (
                    destination_inventory.medicine_id
                ),
                "stock_quantity": (
                    destination_inventory.stock_quantity
                ),
            },
        },
    }


# ============================================================
# GET ALL REDISTRIBUTION REQUESTS
# ============================================================

@router.get("")
def get_redistribution_requests(
    db: Session = Depends(get_db),
):
    rows = (
        db.query(RedistributionRequest)
        .order_by(
            RedistributionRequest.id.desc()
        )
        .all()
    )

    return {
        "success": True,
        "count": len(rows),
        "data": [
            {
                "id": item.id,
                "medicine_id": item.medicine_id,
                "source_phc_id": item.source_phc_id,
                "destination_phc_id": (
                    item.destination_phc_id
                ),
                "quantity": item.quantity,
                "reason": item.reason,
                "status": item.status,
                "created_at": item.created_at,
            }
            for item in rows
        ],
    }
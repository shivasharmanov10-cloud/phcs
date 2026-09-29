
from sqlalchemy.orm import Session

from backend.models.database_models import (
    Inventory,
    PHC,
    Medicine,
    RedistributionRequest,
)


def generate_redistribution_recommendations(
    db: Session,
    *,
    medicine_id: int,
    destination_phc_id: int,
    shortage_quantity: float,
):
    """
    Find active PHCs holding surplus inventory for the requested medicine.

    The service:
    - validates the medicine
    - validates the destination PHC
    - finds active source PHCs
    - preserves 20% of source inventory
    - creates pending redistribution requests
    - returns the created requests
    """

    shortage_quantity = float(shortage_quantity)

    if shortage_quantity <= 0:
        return []

    # --------------------------------------------------------
    # Validate medicine
    # --------------------------------------------------------

    medicine = (
        db.query(Medicine)
        .filter(Medicine.id == medicine_id)
        .first()
    )

    if not medicine:
        return []

    # --------------------------------------------------------
    # Find destination PHC
    # --------------------------------------------------------

    destination = (
        db.query(PHC)
        .filter(
            PHC.id == destination_phc_id,
            PHC.active.is_(True),
        )
        .first()
    )

    if not destination:
        return []

    # --------------------------------------------------------
    # Find source PHCs
    # --------------------------------------------------------

    source_rows = (
        db.query(Inventory, PHC)
        .join(
            PHC,
            PHC.id == Inventory.phc_id,
        )
        .filter(
            Inventory.medicine_id == medicine_id,
            Inventory.phc_id != destination.id,
            PHC.active.is_(True),
            Inventory.stock_quantity > 0,
        )
        .order_by(
            Inventory.stock_quantity.desc()
        )
        .all()
    )

    recommendations = []

    remaining_shortage = shortage_quantity

    # --------------------------------------------------------
    # Build redistribution recommendations
    # --------------------------------------------------------

    for inventory, source_phc in source_rows:

        if remaining_shortage <= 0:
            break

        available_stock = float(
            inventory.stock_quantity
        )

        # Keep 20% of source inventory as safety stock.
        transferable_stock = max(
            0.0,
            available_stock * 0.80,
        )

        transfer_quantity = min(
            remaining_shortage,
            transferable_stock,
        )

        if transfer_quantity <= 0:
            continue

        transfer_quantity = int(
            transfer_quantity
        )

        if transfer_quantity <= 0:
            continue

        reason = (
            f"Redistribute {transfer_quantity} units "
            f"of {medicine.name} from "
            f"{source_phc.phc_id} to "
            f"{destination.phc_id}. "
            f"Destination shortage: "
            f"{shortage_quantity:.2f} units."
        )

        recommendation = RedistributionRequest(
            medicine_id=medicine.id,
            source_phc_id=source_phc.id,
            destination_phc_id=destination.id,
            quantity=transfer_quantity,
            reason=reason,
            status="pending",
        )

        db.add(recommendation)

        recommendations.append(
            recommendation
        )

        remaining_shortage -= transfer_quantity

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    db.commit()

    for recommendation in recommendations:
        db.refresh(recommendation)

    return recommendations
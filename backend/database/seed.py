
from datetime import date, timedelta

from backend.database.database import Base, SessionLocal, engine
from backend.models.database_models import (
    DemandHistory,
    Inventory,
    Medicine,
    PHC,
)


def seed_database():

    # --------------------------------------------------------
    # CREATE TABLES
    # --------------------------------------------------------

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # PHCs
        # ----------------------------------------------------

        phcs = [
            PHC(
                phc_id="PHC001",
                name="Primary Health Centre 001",
                district="Demo District",
                population=10000,
                latitude=26.2183,
                longitude=78.1828,
                active=True,
            ),
            PHC(
                phc_id="PHC002",
                name="Primary Health Centre 002",
                district="Demo District",
                population=12000,
                latitude=26.2250,
                longitude=78.1900,
                active=True,
            ),
            PHC(
                phc_id="PHC003",
                name="Primary Health Centre 003",
                district="Demo District",
                population=8500,
                latitude=26.2100,
                longitude=78.1700,
                active=True,
            ),
        ]

        for phc in phcs:

            existing = (
                db.query(PHC)
                .filter(
                    PHC.phc_id == phc.phc_id
                )
                .first()
            )

            if not existing:
                db.add(phc)

        db.commit()

        # ----------------------------------------------------
        # MEDICINES
        # ----------------------------------------------------

        medicines = [
            Medicine(
                medicine_id="M001",
                name="Paracetamol",
                category="Analgesic",
                unit="units",
                minimum_stock=500,
            ),
            Medicine(
                medicine_id="M002",
                name="Amoxicillin",
                category="Antibiotic",
                unit="units",
                minimum_stock=300,
            ),
            Medicine(
                medicine_id="M003",
                name="ORS",
                category="Rehydration",
                unit="packets",
                minimum_stock=400,
            ),
        ]

        for medicine in medicines:

            existing = (
                db.query(Medicine)
                .filter(
                    Medicine.medicine_id
                    == medicine.medicine_id
                )
                .first()
            )

            if not existing:
                db.add(medicine)

        db.commit()

        # ----------------------------------------------------
        # REFRESH OBJECTS
        # ----------------------------------------------------

        phc_map = {
            p.phc_id: p
            for p in db.query(PHC).all()
        }

        medicine_map = {
            m.medicine_id: m
            for m in db.query(Medicine).all()
        }

        # ----------------------------------------------------
        # INVENTORY
        #
        # PHC001:
        #   M001 = shortage
        #
        # PHC002:
        #   M001 = surplus
        #
        # PHC003:
        #   M001 = moderate stock
        #
        # This gives the redistribution engine
        # a real scenario to calculate.
        # ----------------------------------------------------

        inventory_data = [

            # PHC001 — shortage
            {
                "phc": "PHC001",
                "medicine": "M001",
                "stock": 250,
                "received": 500,
                "expired": 10,
            },

            # PHC002 — surplus
            {
                "phc": "PHC002",
                "medicine": "M001",
                "stock": 3000,
                "received": 3500,
                "expired": 20,
            },

            # PHC003 — moderate
            {
                "phc": "PHC003",
                "medicine": "M001",
                "stock": 900,
                "received": 1000,
                "expired": 5,
            },

            # Other medicines
            {
                "phc": "PHC001",
                "medicine": "M002",
                "stock": 800,
                "received": 900,
                "expired": 10,
            },
            {
                "phc": "PHC002",
                "medicine": "M002",
                "stock": 700,
                "received": 800,
                "expired": 5,
            },
            {
                "phc": "PHC001",
                "medicine": "M003",
                "stock": 1200,
                "received": 1300,
                "expired": 0,
            },
            {
                "phc": "PHC002",
                "medicine": "M003",
                "stock": 900,
                "received": 1000,
                "expired": 0,
            },
        ]

        for item in inventory_data:

            phc = phc_map[item["phc"]]
            medicine = medicine_map[
                item["medicine"]
            ]

            existing = (
                db.query(Inventory)
                .filter(
                    Inventory.phc_id == phc.id,
                    Inventory.medicine_id
                    == medicine.id,
                )
                .first()
            )

            if existing:

                existing.stock_quantity = (
                    item["stock"]
                )

                existing.received_quantity = (
                    item["received"]
                )

                existing.expired_quantity = (
                    item["expired"]
                )

            else:

                db.add(
                    Inventory(
                        phc_id=phc.id,
                        medicine_id=medicine.id,
                        stock_quantity=item["stock"],
                        received_quantity=item[
                            "received"
                        ],
                        expired_quantity=item[
                            "expired"
                        ],
                    )
                )

        db.commit()

        # ----------------------------------------------------
        # DEMAND HISTORY
        # ----------------------------------------------------

        today = date.today()

        for phc in phc_map.values():

            for medicine in medicine_map.values():

                # Don't duplicate existing history.
                existing_count = (
                    db.query(DemandHistory)
                    .filter(
                        DemandHistory.phc_id
                        == phc.id,
                        DemandHistory.medicine_id
                        == medicine.id,
                    )
                    .count()
                )

                if existing_count > 0:
                    continue

                for days_ago in range(1, 15):

                    demand_date = (
                        today
                        - timedelta(
                            days=days_ago
                        )
                    )

                    base_demand = {
                        "M001": 40,
                        "M002": 25,
                        "M003": 35,
                    }.get(
                        medicine.medicine_id,
                        20,
                    )

                    # Small deterministic variation
                    variation = days_ago % 5

                    daily_demand = (
                        base_demand
                        + variation
                    )

                    db.add(
                        DemandHistory(
                            phc_id=phc.id,
                            medicine_id=medicine.id,
                            date=demand_date,
                            daily_demand=daily_demand,
                            population=phc.population,
                        )
                    )

        db.commit()

        print(
            "DATABASE SEED COMPLETE"
        )

    finally:

        db.close()


if __name__ == "__main__":
    seed_database()

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.database import Base


# ============================================================
# PHC
# ============================================================

class PHC(Base):
    __tablename__ = "phcs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    phc_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
    )

    district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    population: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    inventory = relationship(
        "Inventory",
        back_populates="phc",
        cascade="all, delete-orphan",
    )

    demand_history = relationship(
        "DemandHistory",
        back_populates="phc",
        cascade="all, delete-orphan",
    )

# ============================================================
# USER / AUTHENTICATION
# ============================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
    )

    role: Mapped[str] = mapped_column(
        String(50),
        default="viewer",
        index=True,
    )

    # NULL for district-level/admin users.
    # Set for PHC-specific users.
    phc_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "phcs.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )

    phc = relationship("PHC")
# ============================================================
# MEDICINE
# ============================================================

class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    medicine_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    unit: Mapped[str] = mapped_column(
        String(30),
        default="units",
    )

    minimum_stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    inventory = relationship(
        "Inventory",
        back_populates="medicine",
        cascade="all, delete-orphan",
    )

    demand_history = relationship(
        "DemandHistory",
        back_populates="medicine",
        cascade="all, delete-orphan",
    )


# ============================================================
# INVENTORY
# ============================================================

class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    phc_id: Mapped[int] = mapped_column(
        ForeignKey(
            "phcs.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    medicine_id: Mapped[int] = mapped_column(
        ForeignKey(
            "medicines.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    received_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    expired_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    last_updated: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    phc = relationship(
        "PHC",
        back_populates="inventory",
    )

    medicine = relationship(
        "Medicine",
        back_populates="inventory",
    )

    __table_args__ = (
        UniqueConstraint(
            "phc_id",
            "medicine_id",
            name="uq_inventory_phc_medicine",
        ),
    )


# ============================================================
# DEMAND HISTORY
# ============================================================

class DemandHistory(Base):
    __tablename__ = "demand_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    phc_id: Mapped[int] = mapped_column(
        ForeignKey(
            "phcs.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    medicine_id: Mapped[int] = mapped_column(
        ForeignKey(
            "medicines.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    date: Mapped[date] = mapped_column(
        Date,
        index=True,
    )

    daily_demand: Mapped[int] = mapped_column(
        Integer,
    )

    population: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    phc = relationship(
        "PHC",
        back_populates="demand_history",
    )

    medicine = relationship(
        "Medicine",
        back_populates="demand_history",
    )

    __table_args__ = (
        UniqueConstraint(
            "phc_id",
            "medicine_id",
            "date",
            name="uq_demand_phc_medicine_date",
        ),
    )


# ============================================================
# ALERT
# ============================================================

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    phc_id: Mapped[int] = mapped_column(
        ForeignKey(
            "phcs.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    medicine_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "medicines.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    alert_type: Mapped[str] = mapped_column(
        String(50),
    )

    severity: Mapped[str] = mapped_column(
        String(30),
    )

    message: Mapped[str] = mapped_column(
        Text,
    )

    resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


# ============================================================
# REDISTRIBUTION REQUEST
# ============================================================

class RedistributionRequest(Base):
    __tablename__ = "redistribution_requests"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    medicine_id: Mapped[int] = mapped_column(
        ForeignKey(
            "medicines.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    source_phc_id: Mapped[int] = mapped_column(
        ForeignKey(
            "phcs.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    destination_phc_id: Mapped[int] = mapped_column(
        ForeignKey(
            "phcs.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
    )

    reason: Mapped[str] = mapped_column(
        Text,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


# ============================================================
# FEDERATED TRAINING ROUND
# ============================================================

class FederatedRound(Base):
    __tablename__ = "federated_rounds"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    round_number: Mapped[int] = mapped_column(
        Integer,
        unique=True,
    )

    participating_phcs: Mapped[int] = mapped_column(
        Integer,
    )

    samples: Mapped[int] = mapped_column(
        Integer,
    )

    global_mse: Mapped[float] = mapped_column(
        Float,
    )

    global_rmse: Mapped[float] = mapped_column(
        Float,
    )

    algorithm: Mapped[str] = mapped_column(
        String(50),
        default="FedAvg",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


# ============================================================
# ML MODEL
# ============================================================

class MLModel(Base):
    __tablename__ = "ml_models"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
    )

    model_version: Mapped[str] = mapped_column(
        String(50),
    )

    algorithm: Mapped[str] = mapped_column(
        String(100),
    )

    metric_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    metric_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    model_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


# ============================================================
# AI DECISION AUDIT
# ============================================================

class AIDecisionAudit(Base):
    __tablename__ = "ai_decision_audits"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    request_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    phc_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    medicine_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    medicine_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    decision_type: Mapped[str] = mapped_column(
        String(100),
    )

    model_name: Mapped[str] = mapped_column(
        String(255),
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
    )

    predicted_daily_demand: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    current_stock: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    estimated_stock_days: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    risk_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    recommended_order_quantity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    shortage_quantity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    surplus_quantity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    expired_stock_ratio_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )
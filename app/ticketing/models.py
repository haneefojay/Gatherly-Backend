import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import DBBase


class OrderStatus(str, enum.Enum):
    """Order status enumeration"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class TransactionStatus(str, enum.Enum):
    """Transaction status enumeration"""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class RefundStatus(str, enum.Enum):
    """Refund status enumeration"""

    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSED = "processed"


class TicketType(DBBase):
    """Ticket type/category for an event"""

    __tablename__ = "ticket_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default="USD")
    quantity_total = Column(Integer, nullable=False)
    quantity_sold = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    event = relationship("Event", back_populates="ticket_types")
    tiers = relationship("TicketTier", back_populates="ticket_type", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="ticket_type")

    __table_args__ = (
        CheckConstraint("quantity_sold <= quantity_total", name="check_quantity_sold"),
        CheckConstraint("price >= 0", name="check_price_positive"),
        Index("ix_ticket_types_event_active", "event_id", "is_active"),
    )

    def __repr__(self):
        return f"<TicketType {self.name} for event {self.event_id}>"


class TicketTier(DBBase):
    """Ticket pricing tiers (e.g., Early Bird, VIP)"""

    __tablename__ = "ticket_tiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ticket_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price_multiplier = Column(Numeric(5, 2), nullable=False, default=1.00)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket_type = relationship("TicketType", back_populates="tiers")

    __table_args__ = (
        CheckConstraint("price_multiplier > 0", name="check_multiplier_positive"),
        Index("ix_ticket_tiers_type_active", "ticket_type_id", "is_active"),
    )

    def __repr__(self):
        return f"<TicketTier {self.name}>"


class Order(DBBase):
    """Ticket order/purchase"""

    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING, index=True)
    payment_method = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    transaction = relationship("Transaction", back_populates="order", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="check_total_amount_positive"),
       Index("ix_orders_user_created", "user_id", "created_at"),
        Index("ix_orders_status_created", "status", "created_at"),
    )

    def __repr__(self):
        return f"<Order {self.order_number} ({self.status.value})>"


class OrderItem(DBBase):
    """Individual ticket item in an order"""

    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ticket_type_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ticket_types.id"),
        nullable=False,
        index=True
    )
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    order = relationship("Order", back_populates="items")
    ticket_type = relationship("TicketType", back_populates="order_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="check_unit_price_positive"),
        CheckConstraint("subtotal >= 0", name="check_subtotal_positive"),
    )

    def __repr__(self):
        return f"<OrderItem {self.quantity}x {self.ticket_type_id}>"


class Transaction(DBBase):
    """Payment transaction record"""

    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    transaction_id = Column(String(255), unique=True, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING, index=True)
    payment_provider = Column(String(50), nullable=True)
    provider_response = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="transaction")
    refunds = relationship("Refund", back_populates="transaction", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="check_amount_positive"),
        Index("ix_transactions_status_created", "status", "created_at"),
    )

    def __repr__(self):
        return f"<Transaction {self.transaction_id} ({self.status.value})>"


class Refund(DBBase):
    """Refund request and processing"""

    __tablename__ = "refunds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(Enum(RefundStatus), nullable=False, default=RefundStatus.REQUESTED, index=True)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    processed_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    transaction = relationship("Transaction", back_populates="refunds")

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_refund_amount_positive"),
        Index("ix_refunds_status_requested", "status", "requested_at"),
    )

    def __repr__(self):
        return f"<Refund {self.id} ({self.status.value})>"

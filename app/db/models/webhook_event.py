from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            name="uq_webhook_events_event_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    event_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    order_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "orders.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

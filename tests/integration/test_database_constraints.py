from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, WebhookEvent

pytestmark = pytest.mark.integration


def make_order(
    *,
    marketplace: str = "mercadolivre",
    external_order_id: str | None = None,
    total: Decimal | None = None,
) -> Order:
    return Order(
        marketplace=marketplace,
        external_order_id=external_order_id or f"order-{uuid4().hex}",
        status="paid",
        total=total if total is not None else Decimal("249.90"),
    )


async def test_persists_order_with_database_generated_values(
    database_session: AsyncSession,
) -> None:
    order = make_order()

    database_session.add(order)
    await database_session.flush()
    await database_session.refresh(order)

    assert isinstance(order.id, UUID)
    assert order.created_at.tzinfo is not None
    assert order.updated_at.tzinfo is not None


async def test_rejects_duplicate_marketplace_order(
    database_session: AsyncSession,
) -> None:
    external_order_id = f"order-{uuid4().hex}"

    database_session.add(
        make_order(external_order_id=external_order_id),
    )
    await database_session.flush()

    with pytest.raises(IntegrityError) as error:
        async with database_session.begin_nested():
            database_session.add(
                make_order(external_order_id=external_order_id),
            )
            await database_session.flush()

    assert "uq_orders_marketplace_external_order_id" in str(error.value.orig)


async def test_rejects_negative_order_total(
    database_session: AsyncSession,
) -> None:
    with pytest.raises(IntegrityError) as error:
        async with database_session.begin_nested():
            database_session.add(
                make_order(total=Decimal("-0.01")),
            )
            await database_session.flush()

    assert "ck_orders_total_non_negative" in str(error.value.orig)


async def test_rejects_duplicate_webhook_event_id(
    database_session: AsyncSession,
) -> None:
    order = make_order()
    database_session.add(order)
    await database_session.flush()

    event_id = f"event-{uuid4().hex}"

    database_session.add(
        WebhookEvent(
            event_id=event_id,
            order_id=order.id,
        )
    )
    await database_session.flush()

    with pytest.raises(IntegrityError) as error:
        async with database_session.begin_nested():
            database_session.add(
                WebhookEvent(
                    event_id=event_id,
                    order_id=order.id,
                )
            )
            await database_session.flush()

    assert "uq_webhook_events_event_id" in str(error.value.orig)

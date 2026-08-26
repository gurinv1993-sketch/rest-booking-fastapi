from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.booking import Visitors
from schemas.booking import BookingCreate


async def create_in_base(db: AsyncSession, booking_data: BookingCreate) -> Visitors | None:
    # Проверяем занятость только среди активных броней
    query = select(Visitors).where(
        Visitors.booking_date == booking_data.booking_date,
        Visitors.booking_time == booking_data.booking_time,
        Visitors.status == "active"
    )
    res = await db.execute(query)
    existing_booking = res.scalar_one_or_none()
    if existing_booking:
        return None

    # Делаем из пидантик-модели словарь и создаем объект.
    # Статус "active" база подставит сама благодаря default="active" в модели
    db_visitors = Visitors(**booking_data.model_dump())

    db.add(db_visitors)
    await db.commit()
    await db.refresh(db_visitors)
    return db_visitors


async def get_bookings_from_database(db: AsyncSession, filter_date: date = None):
    query = select(Visitors)
    # проверка по дате если она есть
    if filter_date:
        query = query.filter(Visitors.booking_date == filter_date)
    result = await db.execute(query)
    return result.scalars().all()


async def get_booking_by_id(db: AsyncSession, booking_id: int):
    # Ищет одну бронь в базе по ID. Далее возвращает объект брони или None
    booking = await db.get(Visitors, booking_id)
    return booking


async def cancel_booking_in_db(db: AsyncSession, booking_id: int) -> Visitors | None:
    # находим нужную бронь по ID
    booking = await db.get(Visitors, booking_id)
    if not booking:
        return None
    # меняем статус на cancelled (запись остается в базе)
    booking.status = "cancelled"

    # сохраняем
    await db.commit()
    await db.refresh(booking)

    # возвращаем обновленную запись
    return booking
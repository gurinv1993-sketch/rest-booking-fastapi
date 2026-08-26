from datetime import date, datetime
from fastapi import APIRouter, HTTPException
from starlette import status
from core.config import SessionDep
from schemas.booking import BookingCreate, BookingOut
from services.booking_service import create_in_base, get_bookings_from_database, get_booking_by_id, cancel_booking_in_db

router = APIRouter()

@router.post("/bookings", status_code=status.HTTP_201_CREATED, response_model=BookingOut)
async def add_task(booking_data: BookingCreate, db: SessionDep):
    new_booking = await create_in_base(db, booking_data)
    if not new_booking:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Этот слот уже занят"
        )
    return new_booking

@router.get("/bookings", response_model=list[BookingOut])  # Хорошо бы указать список на выход
async def get_bookings(db: SessionDep, booking_date: str | None = None):
    # если пользователь что-то ввел, то проверяем это на верный формат даты
    if booking_date is not None:
        try:
            booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Нееверный формат даты. Попробуйте в формате: гггг-мм-дд"
            )
    # передаем в функцию для get запроса в базу
    res = await get_bookings_from_database(db=db, filter_date=booking_date)
    return res


@router.get("/bookings/{booking_id}", response_model=BookingOut)
async def get_booking(booking_id: int, db: SessionDep):
    # апрашиваем бронь из базы через функцию
    booking = await get_booking_by_id(db=db, booking_id=booking_id)

    # если в базе ничего нет — отдаем 404
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Бронь с ID {booking_id} не найдена"
        )
    # возвращаем строку таблицы, FastAPI сам превратит его в модель BookingOut
    return booking


@router.delete("/bookings/{booking_id}", status_code=status.HTTP_200_OK,
               response_model=BookingOut)
async def cancel_booking(booking_id: int, db: SessionDep):
    # Вызываем асинхронную функцию отмены
    updated_booking = await cancel_booking_in_db(db=db, booking_id=booking_id)

    # если функция вернула None, значит брони с таким ID не существовало
    if updated_booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Бронь с ID {booking_id} не найдена"
        )
    # Возвращаем объект (запись осталась, но статус поменялся)
    return updated_booking
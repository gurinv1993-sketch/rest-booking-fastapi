from datetime import timedelta, date
import pytest
from freezegun import freeze_time
from httpx import AsyncClient
from sqlalchemy import Boolean

def preparation_date(day: int = 0, addition: bool = True) -> str:
    today = date.today()
    if addition:
        max_date = today + timedelta(days=day)
    else:
        max_date = today - timedelta(days=day)
    return max_date.isoformat()

'''декоратор parametrize и код эндпоинта могут быть изредко разделены рубежом 
суток и тест упадет. решение - библиотека freezegun (установка терминалом 
pip install freezegun) временно подменяет стандартный модуль datetime в 
оперативной памяти Python своей фейковой копией на любую глубину запроса'''

'''переменная pytestmark служебная для pytest (она для декораторов серии mark) 
и он применит ее код на все тесты сам. она ждет или один декоратор, 
или список с ними. freeze_time бесполезно прописывать над тестами в ручную так как 
как первой будет выполнен декоратор параметров из за того что содержит вызов функции'''
pytestmark = [
    pytest.mark.freeze_time("2026-09-19"),
    pytest.mark.asyncio
]

@pytest.mark.parametrize("name, value", [
    ("name", "ПС"), ("name", "Тепила Патока"), ("name", "а-"),
("name", "- "), ("name", "St"), ("name", "agibal-philatelex"),
    ("phone", "80000000000"),
    ("booking_date", preparation_date()), ("booking_date", preparation_date(90)),
    ("booking_time", "12:00"), ("booking_time", "22:00"),
    ("guests", "1"), ("guests", "12")])
async def test_add_task(ac: AsyncClient, name: str, value: str): # ac — это httpx.AsyncClient
    temp = {"name": "Мира", "phone": "+79999999999",
     "booking_date": preparation_date(1), "booking_time": "19:00", "guests": "8"}
    temp[name] = value
    res = await ac.post("/bookings", json=temp)
    print("ТЕКСТ ОТВЕТА СЕРВЕРА:", res.text)
    assert res.status_code == 201

@pytest.mark.parametrize("name, value", [
    ("name", "П"), ("name", "-"), ("name", "Виктория$"),
("name", ""), ("name", "G"), ("name", "agibal-philatelex007"),
    ("phone", "801234567890"), ("phone", "70123456789"), ("phone", "80123456789 "),
("phone", " +70123456789"), ("phone", ""),
    ("booking_date", preparation_date(91)), ("booking_date", ""),
("booking_date", preparation_date(1, False)),
    ("booking_time", "11:00"), ("booking_time", "23:00"),
("booking_time", "18:30"), ("booking_time", ""),
    ("guests", "0"), ("guests", "13"), ("guests", ""), ("guests", "5.5")])
async def test_value_error_in_add_task(ac: AsyncClient, name: str, value: str):
    temp = {"name": "Мира", "phone": "+79999999999",
    "booking_date": preparation_date(1), "booking_time": "19:00", "guests": "8"}
    temp[name] = value
    res = await ac.post("/bookings", json=temp)
    print("ТЕКСТ ОТВЕТА СЕРВЕРА:", res.text)
    # Проверяем, что сервер вернул ошибку валидации
    assert res.status_code == 422

async def test_error_conflict_in_add_task(ac: AsyncClient):
    temp = {"name": "Мира", "phone": "+79999999999",
     "booking_date": preparation_date(1), "booking_time": "19:00", "guests": "8"}
    res = await ac.post("/bookings", json=temp)
    res = await ac.post("/bookings", json=temp)
    print("ТЕКСТ ОТВЕТА СЕРВЕРА:", res.text)
    assert res.status_code == 409
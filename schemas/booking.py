import re
from datetime import date, time, timedelta
from pydantic import BaseModel, Field, field_validator, ConfigDict

# базовая модель для проверки данных о брони
class BookingCreate(BaseModel):
    name: str
    phone: str
    booking_date: date
    booking_time: time
    guests: int

    @field_validator('name')
    def validate_name(cls, name: str) -> str:
        pattern = r'^[A-Za-zА-Яа-яёЁ -]{2,}$'
        if not re.match(pattern, name):
            raise ValueError("Неверный формат имени. Нужно ввести минимум 2 символа: только буквы, пробелы, дефис")
        else:
            return name

    @field_validator('phone')
    def validate_phone(cls, phone: str) -> str:
        pattern = r'^(\+7|8)(\d{10})$'
        if not re.match(pattern, phone):
            raise ValueError("Неверный формат телефона. Попробуйте в формате +7XXXXXXXXXX или 8XXXXXXXXXX")
        else:
            return phone

    @field_validator('booking_date')
    def validate_date(cls, booking_date: date) -> date:
        today = date.today()
        max_date = today + timedelta(days=90)
        if booking_date < today:
            raise ValueError("Дата не может быть ранее сегодняшней")
        if booking_date > max_date:
            raise ValueError("Дата не может быть позднее +90 дней")
        return booking_date

    @field_validator('booking_time')
    def validate_time(cls, booking_time: time) -> time:
        if not (12 <= booking_time.hour <= 22):
            raise ValueError("Время должно быть в промежутке от 12:00 до 22:00")
        if booking_time.minute != 0 or booking_time.second != 0:
            raise ValueError("Выбирать можно только ровные часы")
        return booking_time

    @field_validator('guests')
    def validate_guests(cls, guests: int) -> int:
        if not 1 <= guests <= 12:
            raise ValueError("Количество гостей должно быть от 1 до 12 включительно")
        return guests

# модель для ответа пользователю по брони
class BookingOut(BookingCreate):
    id: int
    status: str # 'active' | 'cancelled'

    ''' пидантик ожидает словарь, а ему дадут объект класса таблицы 
    и без этой строки он не разберется'''
    model_config = ConfigDict(from_attributes=True)

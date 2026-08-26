from datetime import date, time
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.config import Model

class Visitors(Model):
    __tablename__ = "visitors"

    # id создает сама БД автоматически
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, index=True)
    phone: Mapped[str] = mapped_column(String(12), index=True)
    booking_date: Mapped[date] = mapped_column(index=True)
    booking_time: Mapped[time]
    guests: Mapped[int]
    status: Mapped[str] = mapped_column(String, default="active")


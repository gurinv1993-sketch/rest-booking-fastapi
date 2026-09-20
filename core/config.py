from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing import Annotated
from fastapi import Depends
import os
from dotenv import load_dotenv

load_dotenv()

# Загружаем адрес базы из файла .env в память программы
DATABASE_URL = os.getenv("DATABASE_URL")

# Создаем асинхронный движок (engine) для работы с файлом БД
engine = create_async_engine(DATABASE_URL, echo=True)

# Создаем фабрику сессий
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Базовый класс для описания моделей
class Model(DeclarativeBase):
    pass

# Наша зависимость (Ассистент), откроет сессию и вернется закрыть
async def get_db():
    async with async_session() as session:
        yield session

# Создаем аннотацию для типа
SessionDep = Annotated[AsyncSession, Depends(get_db)]
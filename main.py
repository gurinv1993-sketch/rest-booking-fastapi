from contextlib import asynccontextmanager
from api.bookings import router as bookings_router
import uvicorn
from fastapi import FastAPI
from core.config import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    from core.config import Model
    import models.booking
    # Мы обращаемся к движку и просим создать все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    print("База данных готова к работе")
    yield  # Разделяет старт и выключение

app = FastAPI(lifespan=lifespan, title="Онлайн-бронирование столика в ресторане")

app.include_router(bookings_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
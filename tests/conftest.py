import pytest
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport

# NullPool — это самый важный инструмент здесь. Он заставляет Docker закрывать сетевое соединение сразу после теста
from sqlalchemy.pool import NullPool

# Импортируем базовую модель (в ней хранится информация обо всех таблицах проекта)
from core.config import Model, get_db
from main import app
from dotenv import load_dotenv

load_dotenv()

# Вытаскиваем секретную ссылку на тестовую базу данных из файла .env (из памяти ОС)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


# Объявляем фикстуру. scope="function" означает, что весь код ниже будет выполняться С НУЛЯ ДЛЯ КАЖДОГО ТЕСТА
@pytest.fixture(scope="function")
async def db_session():
    """Каждый тест получает изолированную сессию, которая полностью очищается после теста"""

    # 1. Создаем асинхронный "движок" подключения к Postgres.
    # poolclass=NullPool — критически важно для Windows! Он запрещает сохранять старые соединения в памяти.
    # Благодаря этому каждый новый тест гарантированно работает в своем чистом цикле событий (Event Loop).
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Если поставить True, в консоль будет сыпаться гигантский лог SQL-запросов
        poolclass=NullPool
    )

    # 2. Создаем фабрику (генератор) сессий.
    # Эта штука сама по себе в базу не ходит, она просто знает чертеж, как создавать сессии AsyncSession.
    testing_session_local = async_sessionmaker(
        bind=test_engine,         # Привязываем фабрику к нашему движку
        expire_on_commit=False,   # Запрещает SQLAlchemy сбрасывать данные из памяти Python после коммита
        class_=AsyncSession       # Указываем, что сессии должны быть строго асинхронными
    )

    # === НАЧАЛО ЭТАПА "ДО ТЕСТА" ===
    # 3. Открываем короткое прямое соединение с Postgres для настройки структуры
    async with test_engine.begin() as conn:
        # run_sync запускает синхронный код создания таблиц внутри асинхронного потока.
        # Команда создает в тестовой Postgres пустые таблицы, описанные в моделях Python.
        await conn.run_sync(Model.metadata.create_all)

    # === ЭТАП "ПЕРЕДАЧА В ТЕСТ" ===
    # 4. Открываем рабочую сессию для выполнения CRUD операций
    async with testing_session_local() as session:
        # yield — важнейшая команда фикстуры. Она ставит этот код НА ПАУЗУ
        # и отдает объект session внутрь тест-функции (например, в test_one_creates_data_in_temporary_db).
        # Пока идет тест, этот код ждет.
        yield session

    # === НАЧАЛО ЭТАПА "ПОСЛЕ ТЕСТА" ===
    # 5. Тест успешно завершился. Мы вышли из блока теста и вернулись сюда.
    # Снова подключаемся к базе, чтобы убраться за собой.
    async with test_engine.begin() as conn:
        # drop_all начисто удаляет ВСЕ таблицы и ВСЕ данные, которые тест успел записать.
        # База данных внутри Docker снова становится идеально пустой, готовой к следующему тесту.
        await conn.run_sync(Model.metadata.drop_all)

    # 6. Окончательно уничтожаем сам движок и обрываем сетевой провод к Docker-контейнеру.
    # Память очищена, никаких зависших процессов не осталось.
    await test_engine.dispose()


@pytest.fixture(scope="function")
async def ac(db_session):  # 1. Фикстура клиента ПРИНИМАЕТ фикстуру сессии базы данных!

    # 2. Магия FastAPI: мы говорим приложению app подменить реальную сессию на тестовую
    # Когда эндпоинт вызовет Depends(get_db) - оригинальную функцию из core.config.py, FastAPI выдаст ему db_session из фикстуры выше
    app.dependency_overrides[get_db] = lambda: db_session

    # 3. Создаем сам клиент, привязанный к нашему настроенному приложению app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client  # Отдаем этот клиент в тест

    # 4. ПОСЛЕ ТЕСТА: Очищаем подмену, чтобы другие тесты или приложение не сломались
    app.dependency_overrides.clear()
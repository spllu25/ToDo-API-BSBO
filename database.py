from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
import os
from dotenv import load_dotenv

try:
    from models import Base, Task
except ImportError:
    class Base(DeclarativeBase):
        pass

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Ключевые настройки для работы с PgBouncer
engine = create_async_engine(
    DATABASE_URL,
    connect_args={
        "statement_cache_size": 0,  # Полностью отключаем кеш подготовленных выражений
        "prepared_statement_cache_size": 0,  # Отключаем подготовленные выражения
        "server_settings": {
            "jit": "off"  # Отключаем JIT компиляцию для стабильности
        }
    },
    # Дополнительные настройки для стабильности
    pool_pre_ping=True,  # Проверяем соединение перед использованием
    pool_recycle=300,    # Переподключаемся каждые 5 минут
    pool_size=5,         # Минимальный размер пула
    max_overflow=10,     # Максимальное количество соединений
    echo=True,           # Включаем логи SQL для отладки
    future=True          # Используем будущие возможности SQLAlchemy
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,      # УБРАЛИ повторяющийся параметр
    expire_on_commit=False,
    class_=AsyncSession
)

async def init_db():
    """Инициализация базы данных с обработкой ошибок"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ База данных инициализирована!")
            return
        except Exception as e:
            print(f"⚠️ Попытка {attempt + 1}/{max_retries} не удалась: {e}")
            if attempt == max_retries - 1:
                print("❌ Не удалось инициализировать БД после нескольких попыток")
                raise

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
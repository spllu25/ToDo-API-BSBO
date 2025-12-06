from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from database import init_db, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from routers import tasks, stats, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Запуск приложения...")
    print("Инициализация базы данных...")
    
    try:
        await init_db()
        print("База данных инициализирована!")
    except Exception as e:
        print(f"Ошибка инициализации БД: {e}")
        print("Продолжаем без базы данных...")
    
    print("Приложение готово к работе!")
    yield 
    print("Остановка приложения...")

app = FastAPI(
    title="ToDo лист API",
    description="API для управления задачами с использованием матрицы Эйзенхауэра",
    version="2.0.0",
    contact={
        "name": "Ваше Имя",
    },
    lifespan=lifespan
)

app.include_router(auth.router, prefix="/api/v3")
app.include_router(tasks.router, prefix="/api/v3")
app.include_router(stats.router, prefix="/api/v3")

@app.get("/")
async def read_root() -> dict:
    return {
        "message": "Task Manager API - Управление задачами по матрице Эйзенхауэра",
        "version": "2.0.0",
        "database": "PostgreSQL (Supabase)",
        "docs": "/docs",
        "redoc": "/redoc",
    }

@app.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_async_session)
) -> dict:
    """
    Проверка здоровья API и динамическая проверка подключения к БД.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status
    }
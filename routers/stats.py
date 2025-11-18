from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timezone
from typing import List

from models import Task
from database import get_async_session

router = APIRouter(
    prefix="/stats",
    tags=["statistics"]
)

@router.get("/", response_model=dict)
async def get_tasks_stats(db: AsyncSession = Depends(get_async_session)) -> dict:
    result = await db.execute(select(Task))
    tasks = result.scalars().all()
    total_tasks = len(tasks)
    by_quadrant = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    by_status = {"completed": 0, "pending": 0}

    for task in tasks:
        if task.quadrant in by_quadrant:
            by_quadrant[task.quadrant] += 1
        if task.completed:
            by_status["completed"] += 1
        else:
            by_status["pending"] += 1
    return {
        "total_tasks": total_tasks,
        "by_quadrant": by_quadrant,
        "by_status": by_status
    }

# НОВЫЙ ЭНДПОИНТ - Статистика по дедлайнам
@router.get("/deadlines")
async def get_deadline_stats(db: AsyncSession = Depends(get_async_session)):
    """Статистика по срокам выполнения задач со статусом 'pending'"""
    today = datetime.now(timezone.utc).date()
    
    # Получить все незавершенные задачи с дедлайном
    result = await db.execute(
        select(Task).where(
            and_(
                Task.completed == False,
                Task.deadline_at.isnot(None)
            )
        )
    )
    pending_tasks = result.scalars().all()
    
    stats = []
    for task in pending_tasks:
        if task.deadline_at:
            if task.deadline_at.tzinfo:
                deadline_date = task.deadline_at.astimezone(timezone.utc).date()
            else:
                deadline_date = task.deadline_at.date()
            
            days_remaining = (deadline_date - today).days
            
            stats.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "created_at": task.created_at,
                "deadline_at": task.deadline_at,
                "days_remaining": days_remaining
            })
    
    return {
        "today": today.isoformat(),
        "total_pending_tasks_with_deadlines": len(stats),
        "tasks": sorted(stats, key=lambda x: x["days_remaining"])
    }
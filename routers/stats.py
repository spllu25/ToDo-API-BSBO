
from datetime import datetime, timezone

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database import get_async_session
from models import User, Task
from schemas_auth import UserResponse
from dependencies import get_current_user, get_current_admin
from pydantic import BaseModel

router = APIRouter(
    prefix="/stats",
    tags=["statistics"]
)

@router.get("/", response_model=dict)
async def get_tasks_stats(db: AsyncSession = Depends(get_async_session),
                          current_user: User = Depends(get_current_user)
                          ) -> dict:
    if current_user.role.value == 'admin':
        result = await db.execute(select(Task))
    else:
        result = await db.execute(select(Task).where(Task.user_id == current_user.id))
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

#  Статистика по дедлайнам
@router.get("/deadlines")
async def get_deadline_stats(db: AsyncSession = Depends(get_async_session),
                             current_user: User = Depends(get_current_user)):
    """Статистика по срокам выполнения задач со статусом 'pending'"""
    today = datetime.now(timezone.utc).date()
    
    if current_user.role.value == 'admin':
        result = await db.execute(
            select(Task).where(
                and_(
                    Task.completed == False,
                    Task.deadline_at.isnot(None)
                )
            )
        )
    else:
        result = await db.execute(
            select(Task).where(
                and_(
                    Task.user_id == current_user.id,
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


class UserWithTasksCount(BaseModel):
    id: int
    nickname: str
    email: str
    role: str
    created_at: Optional[str] = None
    tasks_count: int
    
    class Config:
        from_attributes = True

@router.get("/users", response_model=List[UserWithTasksCount])
async def get_all_users(
    db: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin)
) -> List[UserWithTasksCount]:
    """
    Получить список всех пользователей с количеством их задач
    
    Доступно только администраторам
    """
    stmt = select(
        User.id,
        User.nickname,
        User.email,
        User.role,
        func.count(Task.id).label('tasks_count')
    ).join(
        Task, User.id == Task.user_id, isouter=True
    ).group_by(User.id)
    
    result = await db.execute(stmt)
    users_with_counts = result.all()
    
    users_list = []
    for user in users_with_counts:
        users_list.append(UserWithTasksCount(
            id=user.id,
            nickname=user.nickname,
            email=user.email,
            role=user.role.value if hasattr(user.role, 'value') else user.role,
            tasks_count=user.tasks_count
        ))
    
    return users_list
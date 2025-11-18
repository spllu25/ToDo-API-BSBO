from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from database import get_async_session
from models import Task
from schemas import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {'description': 'Task not found'}},
)

# Вспомогательные функции для расчетов
def calculate_urgency(deadline_at: Optional[datetime]) -> bool:
    """Рассчитать срочность задачи (True если до дедлайна <= 3 дня)"""
    if not deadline_at:
        return False
    
    today = datetime.now(timezone.utc).date()
    if deadline_at.tzinfo:
        deadline_date = deadline_at.astimezone(timezone.utc).date()
    else:
        deadline_date = deadline_at.date()
    
    days_until_deadline = (deadline_date - today).days
    return days_until_deadline <= 3

def calculate_quadrant(is_important: bool, deadline_at: Optional[datetime]) -> str:
    """Рассчитать квадрант матрицы Эйзенхауэра"""
    is_urgent = calculate_urgency(deadline_at)
    
    if is_important and is_urgent:
        return "Q1"
    elif is_important and not is_urgent:
        return "Q2"
    elif not is_important and is_urgent:
        return "Q3"
    else:
        return "Q4"

def calculate_days_until_deadline(deadline_at: Optional[datetime]) -> Optional[int]:
    """Рассчитать количество дней до дедлайна"""
    if not deadline_at:
        return None
    
    today = datetime.now(timezone.utc).date()
    if deadline_at.tzinfo:
        deadline_date = deadline_at.astimezone(timezone.utc).date()
    else:
        deadline_date = deadline_at.date()
    
    return (deadline_date - today).days

# GET ALL TASKS - Получить все задачи
@router.get("", response_model=List[TaskResponse])
async def get_all_tasks(
    db: AsyncSession = Depends(get_async_session)
) -> List[TaskResponse]:
    result = await db.execute(select(Task))
    tasks = result.scalars().all()
    
    # Преобразуем задачи с расчетными полями
    response_tasks = []
    for task in tasks:
        is_urgent = calculate_urgency(task.deadline_at)
        days_until_deadline = calculate_days_until_deadline(task.deadline_at)
        
        response_tasks.append(TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            is_important=task.is_important,
            deadline_at=task.deadline_at,
            quadrant=task.quadrant,
            is_urgent=is_urgent,
            days_until_deadline=days_until_deadline,
            completed=task.completed,
            created_at=task.created_at,
            completed_at=task.completed_at
        ))
    
    return response_tasks

# SEARCH TASKS - Поиск задач 
@router.get("/search", response_model=List[TaskResponse])
async def search_tasks(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_async_session)
) -> List[TaskResponse]:
    keyword = f"%{q.lower()}%"
    
    result = await db.execute(
        select(Task).where(
            (Task.title.ilike(keyword)) |
            (Task.description.ilike(keyword))
        )
    )
    tasks = result.scalars().all()

    if not tasks:
        raise HTTPException(status_code=404, detail="По данному запросу ничего не найдено")
    
    # Добавляем расчетные поля
    response_tasks = []
    for task in tasks:
        is_urgent = calculate_urgency(task.deadline_at)
        days_until_deadline = calculate_days_until_deadline(task.deadline_at)
        
        response_tasks.append(TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            is_important=task.is_important,
            deadline_at=task.deadline_at,
            quadrant=task.quadrant,
            is_urgent=is_urgent,
            days_until_deadline=days_until_deadline,
            completed=task.completed,
            created_at=task.created_at,
            completed_at=task.completed_at
        ))
    
    return response_tasks

# GET TASKS BY QUADRANT - Получить задачи по квадранту
@router.get("/quadrant/{quadrant}", response_model=List[TaskResponse])
async def get_tasks_by_quadrant(
    quadrant: str,
    db: AsyncSession = Depends(get_async_session)
) -> List[TaskResponse]:
    if quadrant not in ["Q1", "Q2", "Q3", "Q4"]:
        raise HTTPException(
            status_code=400,
            detail="Неверный квадрант. Используйте: Q1, Q2, Q3, Q4"
        )
    
    result = await db.execute(
        select(Task).where(Task.quadrant == quadrant)
    )
    tasks = result.scalars().all()
    
    # Добавляем расчетные поля
    response_tasks = []
    for task in tasks:
        is_urgent = calculate_urgency(task.deadline_at)
        days_until_deadline = calculate_days_until_deadline(task.deadline_at)
        
        response_tasks.append(TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            is_important=task.is_important,
            deadline_at=task.deadline_at,
            quadrant=task.quadrant,
            is_urgent=is_urgent,
            days_until_deadline=days_until_deadline,
            completed=task.completed,
            created_at=task.created_at,
            completed_at=task.completed_at
        ))
    
    return response_tasks

# GET TASKS BY STATUS - Получить задачи по статусу
@router.get("/status/{status}", response_model=List[TaskResponse])
async def get_tasks_by_status(
    status: str,
    db: AsyncSession = Depends(get_async_session)
) -> List[TaskResponse]:
    if status not in ["completed", "pending"]:
        raise HTTPException(
            status_code=400,
            detail="Недопустимый статус. Используйте: completed или pending"
        )

    is_completed = (status == "completed")
    result = await db.execute(
        select(Task).where(Task.completed == is_completed)
    )
    tasks = result.scalars().all()
    
    # Добавляем расчетные поля
    response_tasks = []
    for task in tasks:
        is_urgent = calculate_urgency(task.deadline_at)
        days_until_deadline = calculate_days_until_deadline(task.deadline_at)
        
        response_tasks.append(TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            is_important=task.is_important,
            deadline_at=task.deadline_at,
            quadrant=task.quadrant,
            is_urgent=is_urgent,
            days_until_deadline=days_until_deadline,
            completed=task.completed,
            created_at=task.created_at,
            completed_at=task.completed_at
        ))
    
    return response_tasks

# GET TASK BY ID - Получить задачу по ID
@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: int,
    db: AsyncSession = Depends(get_async_session)
) -> TaskResponse:
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Добавляем расчетные поля
    is_urgent = calculate_urgency(task.deadline_at)
    days_until_deadline = calculate_days_until_deadline(task.deadline_at)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        is_important=task.is_important,
        deadline_at=task.deadline_at,
        quadrant=task.quadrant,
        is_urgent=is_urgent,
        days_until_deadline=days_until_deadline,
        completed=task.completed,
        created_at=task.created_at,
        completed_at=task.completed_at
    )

# POST - СОЗДАНИЕ НОВОЙ ЗАДАЧИ
@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_async_session)
) -> TaskResponse:
    # Рассчитываем квадрант на основе важности и дедлайна
    quadrant = calculate_quadrant(task.is_important, task.deadline_at)

    new_task = Task(
        title=task.title,
        description=task.description,
        is_important=task.is_important,
        deadline_at=task.deadline_at,
        quadrant=quadrant,
        completed=False
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    # Добавляем расчетные поля для ответа
    is_urgent = calculate_urgency(new_task.deadline_at)
    days_until_deadline = calculate_days_until_deadline(new_task.deadline_at)
    
    return TaskResponse(
        id=new_task.id,
        title=new_task.title,
        description=new_task.description,
        is_important=new_task.is_important,
        deadline_at=new_task.deadline_at,
        quadrant=new_task.quadrant,
        is_urgent=is_urgent,
        days_until_deadline=days_until_deadline,
        completed=new_task.completed,
        created_at=new_task.created_at,
        completed_at=new_task.completed_at
    )

# PUT - ОБНОВЛЕНИЕ ЗАДАЧИ
@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_async_session)
) -> TaskResponse:
    # ШАГ 1: Ищем задачу по ID
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    # ШАГ 2: Получаем и обновляем только переданные поля
    update_data = task_update.model_dump(exclude_unset=True)

    # ШАГ 3: Обновить атрибуты объекта
    for field, value in update_data.items():
        setattr(task, field, value)

    # ШАГ 4: Пересчитываем квадрант, если изменились важность или дедлайн
    if "is_important" in update_data or "deadline_at" in update_data:
        task.quadrant = calculate_quadrant(task.is_important, task.deadline_at)

    await db.commit()
    await db.refresh(task)

    # Добавляем расчетные поля для ответа
    is_urgent = calculate_urgency(task.deadline_at)
    days_until_deadline = calculate_days_until_deadline(task.deadline_at)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        is_important=task.is_important,
        deadline_at=task.deadline_at,
        quadrant=task.quadrant,
        is_urgent=is_urgent,
        days_until_deadline=days_until_deadline,
        completed=task.completed,
        created_at=task.created_at,
        completed_at=task.completed_at
    )

# PATCH - ОТМЕТИТЬ ЗАДАЧУ ВЫПОЛНЕННОЙ
@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session)
) -> TaskResponse:
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    task.completed = True
    task.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(task)

    # Добавляем расчетные поля для ответа
    is_urgent = calculate_urgency(task.deadline_at)
    days_until_deadline = calculate_days_until_deadline(task.deadline_at)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        is_important=task.is_important,
        deadline_at=task.deadline_at,
        quadrant=task.quadrant,
        is_urgent=is_urgent,
        days_until_deadline=days_until_deadline,
        completed=task.completed,
        created_at=task.created_at,
        completed_at=task.completed_at
    )

# DELETE - УДАЛЕНИЕ ЗАДАЧИ
@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session)
) -> dict:
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    deleted_task_info = {
        "id": task.id,
        "title": task.title
    }
    
    await db.delete(task)
    await db.commit()

    return {
        "message": "Задача успешно удалена",
        "id": deleted_task_info["id"],
        "title": deleted_task_info["title"]
    }
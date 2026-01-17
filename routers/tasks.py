from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from utils import calculate_urgency, calculate_days_until_deadline, calculate_quadrant
from database import get_async_session
from models import Task, User
from schemas import TaskCreate, TaskResponse, TaskUpdate
from dependencies import get_current_user

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {'description': 'Task not found'}},
)


# GET ALL TASKS - Получить все задачи
@router.get("", response_model=List[TaskResponse])
async def get_all_tasks(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[TaskResponse]:
    if current_user.role.value == "admin":
        result = await db.execute(select(Task))
    else:
        result = await db.execute(select(Task).where(Task.user_id == current_user.id))
    
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
            completed_at=task.completed_at,
            user_id = task.user_id
        ))
    
    return response_tasks

# SEARCH TASKS - Поиск задач 
@router.get("/search", response_model=List[TaskResponse])
async def search_tasks(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[TaskResponse]:
    keyword = f"%{q.lower()}%"
    
    if current_user.role.value == "admin":
        result = await db.execute(
            select(Task).where(
                (Task.title.ilike(keyword)) |
                (Task.description.ilike(keyword))
            )
    )
    else:
        result = await db.execute(
            select(Task).where(
                Task.user_id == current_user.id,
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
            completed_at=task.completed_at,
            user_id = task.user_id
        ))
    
    return response_tasks

# GET TASKS BY QUADRANT - Получить задачи по квадранту
@router.get("/quadrant/{quadrant}", response_model=List[TaskResponse])
async def get_tasks_by_quadrant(
    quadrant: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[TaskResponse]:
    if quadrant not in ["Q1", "Q2", "Q3", "Q4"]:
        raise HTTPException(
            status_code=400,
            detail="Неверный квадрант. Используйте: Q1, Q2, Q3, Q4"
        )
    
    if current_user.role.value == 'admin':
        result = await db.execute(
            select(Task).where(Task.quadrant == quadrant)
        )
    else:
        result = await db.execute(
            select(Task).where(Task.quadrant == quadrant,
                               Task.user_id == current_user.id)
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
            completed_at=task.completed_at,
            user_id = task.user_id
        ))
    
    return response_tasks

# GET TASKS BY STATUS - Получить задачи по статусу
@router.get("/status/{status}", response_model=List[TaskResponse])
async def get_tasks_by_status(
    status: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[TaskResponse]:
    if status not in ["completed", "pending"]:
        raise HTTPException(
            status_code=400,
            detail="Недопустимый статус. Используйте: completed или pending"
        )

    is_completed = (status == "completed")

    if current_user.role.value == 'admin':
        result = await db.execute(
            select(Task).where(Task.completed == is_completed)
        )
    else:
        result = await db.execute(
        select(Task).where(Task.completed == is_completed,
                           Task.user_id == current_user.id)
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
            completed_at=task.completed_at,
            user_id = task.user_id
        ))
    
    return response_tasks

# GET TASK BY ID - Получить задачу по ID
@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    if current_user.role.value == 'admin':
        result = await db.execute(
            select(Task).where(Task.id == task_id)
        )
    else:
        result = await db.execute(
        select(Task).where(Task.id == task_id,
                           Task.user_id == current_user.id)
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
        completed_at=task.completed_at,
        user_id = task.user_id
    )

# POST - СОЗДАНИЕ НОВОЙ ЗАДАЧИ
@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    # Рассчитываем квадрант на основе важности и дедлайна
    quadrant = calculate_quadrant(task.is_important, task.deadline_at)

    new_task = Task(
        title=task.title,
        description=task.description,
        is_important=task.is_important,
        deadline_at=task.deadline_at,
        quadrant=quadrant,
        completed=False,
        user_id = current_user.id
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
        is_urgent=is_urgent,  # Расчетное поле для ответа
        days_until_deadline=days_until_deadline,
        completed=new_task.completed,
        created_at=new_task.created_at,
        completed_at=new_task.completed_at,
        user_id = new_task.user_id
    )

# PUT - ОБНОВЛЕНИЕ ЗАДАЧИ
@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if current_user.role.value != 'admin' and task.user_id!= current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой задаче")
    
    update_data = task_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(task, field, value)

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
        completed_at=task.completed_at,
        user_id = task.user_id
    )

# @router.patch("/{task_id}/complete", response_model=TaskResponse)
# async def complete_task(
#     task_id: int,
#     db: AsyncSession = Depends(get_async_session),
#     current_user: User = Depends(get_current_user)
# ) -> TaskResponse:
#     result = await db.execute(
#         select(Task).where(Task.id == task_id)
#     )
#     task = result.scalar_one_or_none()
    
#     if not task:
#         raise HTTPException(status_code=404, detail="Задача не найдена")

#     if current_user.role.value != 'admin' and task.user_id != current_user.id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Нет доступа к этой задаче"
#         )

#     # 🔁 TOGGLE completed
#     if task.completed:
#         task.completed = False
#         task.completed_at = None
#     else:
#         task.completed = True
#         task.completed_at = datetime.now(timezone.utc)

#     await db.commit()
#     await db.refresh(task)

#     is_urgent = calculate_urgency(task.deadline_at)
#     days_until_deadline = calculate_days_until_deadline(task.deadline_at)
    
#     return TaskResponse(
#         id=task.id,
#         title=task.title,
#         description=task.description,
#         is_important=task.is_important,
#         deadline_at=task.deadline_at,
#         quadrant=task.quadrant,
#         is_urgent=is_urgent,
#         days_until_deadline=days_until_deadline,
#         completed=task.completed,
#         created_at=task.created_at,
#         completed_at=task.completed_at,
#         user_id=task.user_id
#     )

@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def toggle_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    task.completed = not task.completed
    task.completed_at = datetime.now(timezone.utc) if task.completed else None

    await db.commit()
    await db.refresh(task)
    return task


# DELETE - УДАЛЕНИЕ ЗАДАЧИ
@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> dict:
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    if current_user.role.value != 'admin' and task.user_id!= current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой задаче")
    
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

# GET TASKS (TODAY) - Получить задачи, срок которых истекает сегодня
@router.get("/today", response_model=List[TaskResponse])
async def get_tasks_due_today(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[TaskResponse]:
    """Получить задачи, срок выполнения которых истекает сегодня"""
    today = datetime.now(timezone.utc).date()
    
    if current_user.role.value == 'admin':
        result = await db.execute(
            select(Task).where(
                Task.deadline_at.isnot(None),
                Task.completed == False
            )
        )
    else:
        result = await db.execute(
            select(Task).where(
                Task.user_id == current_user.id,
                Task.deadline_at.isnot(None),
                Task.completed == False
            )
        )

    tasks = result.scalars().all()
    
    today_tasks = []
    for task in tasks:
        if task.deadline_at:
            if task.deadline_at.tzinfo:
                deadline_date = task.deadline_at.astimezone(timezone.utc).date()
            else:
                deadline_date = task.deadline_at.date()
            
            if deadline_date == today:
                today_tasks.append(task)
    
    response_tasks = []
    for task in today_tasks:
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
            completed_at=task.completed_at,
            user_id = task.user_id
        ))
    
    return response_tasks
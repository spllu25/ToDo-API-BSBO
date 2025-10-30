from fastapi import APIRouter
from fastapi import HTTPException, Query, Response, status
from datetime import datetime
from database import tasks_db
from schemas import TaskBase, TaskCreate, TaskResponse, TaskUpdate


router = APIRouter(
    prefix="/stats",
    tags=["stats"],
    responses={404:{'description':'Task not found'}},
)

@router.get("")
async def get_all_tasks() -> dict:
    return {
        "count": len(tasks_db), 
        "tasks": tasks_db 
}

# Endpoint для поиска задач по ключевому слову
@router.get("/search")
async def search_tasks(q: str) -> dict:
    if len(q) < 2:
        raise HTTPException(
            status_code=400,
            detail="Ключевое слово должно содержать минимум 2 символа"
        )
    
    search_results = [
        task for task in tasks_db
        if (task["title"] and q.lower() in task["title"].lower()) or
           (task["description"] and q.lower() in task["description"].lower())
    ]
    
    if not search_results:
        raise HTTPException(
            status_code=404,
            detail=f"Задачи по запросу '{q}' не найдены"
        )
    
    return {
        "query": q,
        "count": len(search_results),
        "tasks": search_results
    }


# Endpoint для получения статистики по задачам
@router.get("/stats")
async def get_tasks_stats() -> dict:
    by_quadrant = {
        "Q1": len([task for task in tasks_db if task["quadrant"] == "Q1"]),
        "Q2": len([task for task in tasks_db if task["quadrant"] == "Q2"]),
        "Q3": len([task for task in tasks_db if task["quadrant"] == "Q3"]),
        "Q4": len([task for task in tasks_db if task["quadrant"] == "Q4"])
    }
    
    completed_tasks = len([task for task in tasks_db if task["completed"]])
    pending_tasks = len([task for task in tasks_db if not task["completed"]])
    
    return {
        "total_tasks": len(tasks_db),
        "by_quadrant": by_quadrant,
        "by_status": {
            "completed": completed_tasks,
            "pending": pending_tasks
        }
    }


@router.get("/quadrant/{quadrant}")
async def get_tasks_by_quadrant(quadrant: str) -> dict:
    if quadrant not in ["Q1", "Q2", "Q3", "Q4"]:
        raise HTTPException( 
            status_code=400,
            detail="Неверный квадрант. Используйте: Q1, Q2, Q3, Q4" 
)
    filtered_tasks = [
        task 
        for task in tasks_db 
        if task["quadrant"] == quadrant
    ]

    return {
        "quadrant": quadrant,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }


# Endpoint для фильтрации задач по статусу выполнения
@router.get("/status/{status}")
async def get_tasks_by_status(status: str) -> dict:
    if status not in ["completed", "pending"]:
        raise HTTPException(
            status_code=400,
            detail="Неверный статус. Используйте: 'completed' или 'pending'"
        )
    
    is_completed = (status == "completed")
    
    filtered_tasks = [
        task for task in tasks_db 
        if task["completed"] == is_completed
    ]
    
    if not filtered_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Задачи со статусом '{status}' не найдены"
        )
    
    return {
        "status": status,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }

# Endpoint для получения задачи по ID
@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(task_id: int) -> TaskResponse:
    task = next((task for task in tasks_db if task["id"] == task_id), None)
    
    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Задача с ID {task_id} не найдена"
        )
    
    return task

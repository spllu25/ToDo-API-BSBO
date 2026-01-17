from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, timezone


# Базовая схема для Task
class TaskBase(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Название задачи")
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Описание задачи")
    is_important: bool = Field(
        ...,
        description="Важность задачи")
    deadline_at: Optional[datetime] = Field(  # НОВОЕ ПОЛЕ
        None,
        description="Плановый срок выполнения задачи")

# Схема для создания новой задачи
class TaskCreate(TaskBase):
    @validator("deadline_at")
    def deadline_must_be_future(cls, v):
        if v is None:
            return v

    # если пришла дата БЕЗ timezone — считаем, что это UTC
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)

        if v <= datetime.now(timezone.utc):
            raise ValueError("Дедлайн должен быть в будущем")

        return v

# Схема для обновления задачи
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        description="Новое название задачи")
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Новое описание")
    is_important: Optional[bool] = Field(
        None,
        description="Новая важность")
    deadline_at: Optional[datetime] = Field(  # НОВОЕ ПОЛЕ
        None,
        description="Новый дедлайн")
    completed: Optional[bool] = Field(
        None,
        description="Статус выполнения")

# Модель для ответа
class TaskResponse(TaskBase):
    id: int = Field(
        ...,
        description="Уникальный идентификатор задачи",
        examples=[1])
    quadrant: str = Field(
        ...,
        description="Квадрант матрицы Эйзенхауэра (Q1, Q2, Q3, Q4)",
        examples=["Q1"])
    is_urgent: bool = Field(  # Теперь расчетное поле
        ...,
        description="Расчетная срочность задачи")
    days_until_deadline: Optional[int] = Field(  # НОВОЕ ПОЛЕ
        None,
        description="Количество дней до дедлайна")
    completed: bool = Field(
        default=False,
        description="Статус выполнения задачи")
    created_at: datetime = Field(
        ...,
        description="Дата и время создания задачи")
    completed_at: Optional[datetime] = Field(
        None,
        description="Дата и время завершения задачи")

    class Config:
        from_attributes = True



class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    password: Optional[str] = None

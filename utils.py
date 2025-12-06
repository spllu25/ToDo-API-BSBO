from datetime import datetime, timezone
from typing import Optional

def calculate_urgency(deadline_at: Optional[datetime]) -> bool:
    """Рассчитать срочность задачи (True если до дедлайна <= 3 дня)"""
    if deadline_at is None:
        return False
    
    now = datetime.now(timezone.utc)
    
    if deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(tzinfo=timezone.utc)
    
    time_difference = deadline_at - now
    days_until_deadline = time_difference.days
    
    return days_until_deadline <= 3

def calculate_days_until_deadline(deadline_at: Optional[datetime]) -> Optional[int]:
    """Рассчитать количество дней до дедлайна"""
    if deadline_at is None:
        return None
    
    now = datetime.now(timezone.utc)
    
    if deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(tzinfo=timezone.utc)
    
    time_difference = deadline_at - now
    return time_difference.days

def calculate_quadrant(is_important: bool, deadline_at: Optional[datetime]) -> str:
    """Рассчитать квадрант матрицы Эйзенхауэра на основе важности и дедлайна"""
    is_urgent = calculate_urgency(deadline_at)
    
    if is_important and is_urgent:
        return "Q1"  # Важно и срочно
    elif is_important and not is_urgent:
        return "Q2"  # Важно, но не срочно
    elif not is_important and is_urgent:
        return "Q3"  # Не важно, но срочно
    else:
        return "Q4"  # Не важно и не срочно
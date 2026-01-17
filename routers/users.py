from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_async_session
from dependencies import get_current_user
from models import User
from schemas_user import UserUpdate
from auth_utils import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "nickname": current_user.nickname,
        "email": current_user.email,
        "role": current_user.role.value
    }

@router.put("/me")
async def update_me(
    data: UserUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    if data.nickname:
        current_user.nickname = data.nickname

    if data.password:
        current_user.hashed_password = get_password_hash(data.password)

    await db.commit()
    return {"message": "Профиль обновлён"}

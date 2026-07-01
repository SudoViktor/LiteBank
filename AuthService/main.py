from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import engine, Base, get_db
from models import User
from schemas import UserCreate, UserResponse

app = FastAPI(title="Auth Service API")

@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # У реальному житті тут ще має бути хешування пароля (наприклад, через passlib)
    new_user = User(username=user.username, password_hash=user.password)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)  # Отримуємо з бази згенерований ID

    return new_user


@app.get("/users/", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
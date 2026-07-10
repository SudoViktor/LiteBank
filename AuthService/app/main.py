from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_db
from app.models import User
from app.config import create_access_token

app = FastAPI(title="Auth API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
async def root():
    return {"message": "Сервер Auth працює 345345! 🚀"}

# Перевіряємо, чи жива база
@app.get("/db-ping")
async def ping_db(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {"status": "База даних підключена успішно!", "result": result.scalar()}


class UserInfo(BaseModel):
    username: str
    password: str

@app.post("/register")
async def register(user_data: UserInfo, db: AsyncSession = Depends(get_db)):
    # Викликаємо нашу асинхронну функцію
    user = await User.create_user(db=db, username=user_data.username, password=user_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="A user with this name already exists.")


    return {"message": "User successfully created!", "user_id": user.id}


@app.post("/login")
async def login(user_data: UserInfo, db: AsyncSession = Depends(get_db)):
    user = await User.get_by_username(db, user_data.username)
    if not user or not user.check_password(user_data.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    data = {"sub": user_data.username}
    token = create_access_token(data)

    return {
        "access_token": token,
        "token_type": "bearer"
    }
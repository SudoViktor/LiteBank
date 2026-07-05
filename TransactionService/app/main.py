from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.config import get_current_user

app = FastAPI(title="Transactions API")

@app.get("/")
async def root():
    return {"message": "Сервер Auth працює! 🚀"}

@app.get("/my-accounts")
async def get_my_accounts(current_user: str = Depends(get_current_user)):
    return {
        "message": "Ти успішно пройшов авторизацію!",
        "user": current_user,
        "accounts": ["UA123...", "UA999..."]
    }
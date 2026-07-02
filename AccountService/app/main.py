from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db

app = FastAPI(title="Mini Bank API")

@app.get("/")
async def root():
    return {"message": "Сервер працює! 🚀"}

# Перевіряємо, чи жива база
@app.get("/db-ping")
async def ping_db(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {"status": "База даних підключена успішно!", "result": result.scalar()}
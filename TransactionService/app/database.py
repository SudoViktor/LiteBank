import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv(
    "http://host.docker.internal:5432/",
    "postgresql+asyncpg://transactions_user:transactions_pass123@localhost:5432/transactions_db"
)
# Створюємо двигун
engine = create_async_engine(DATABASE_URL, echo=True)

# Фабрика сесій
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Залежність для FastAPI (щоб отримувати сесію в ендпоінтах)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
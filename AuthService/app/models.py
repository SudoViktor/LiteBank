from sqlalchemy import Column, Integer, String
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)


    def set_password(self, password: str):
        """Хешує пароль і зберігає його в модель"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Перевіряє, чи співпадає пароль із хешем"""
        return check_password_hash(self.password_hash, password)

    @staticmethod
    async def get_by_username(db: AsyncSession, username):
        query = select(User).where(User.username == username)
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            return existing_user
        return None

    @staticmethod
    async def create_user(db: AsyncSession, username: str, password: str):
        # 1. Перевіряємо, чи існує вже такий користувач
        query = select(User).where(User.username == username)
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            return None  # Або можна викликати raise HTTPException(status_code=400)

        new_user = User(username=username)
        new_user.set_password(password)

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
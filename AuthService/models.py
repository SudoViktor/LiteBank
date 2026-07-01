from sqlalchemy import Column, String, Integer
from database import Base

# Змінив моделі? Зроби:
# docker-compose exec auth-service alembic revision --autogenerate -m "-"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    phone = Column(String, unique=True)
    password_hash = Column(String, nullable=False)
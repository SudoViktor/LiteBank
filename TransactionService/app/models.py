from sqlalchemy import Column, Integer, String
from app.database import Base


class Transactions(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    from_account = Column(String)
    to_account = Column(String)
    status = Column(String)
    amount = Column(String)
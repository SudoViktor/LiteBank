from sqlalchemy import Column, Integer, String, or_, and_
from app.database import Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# alembic upgrade head && alembic revision --autogenerate -m "-" &&

class Owner(Base):
    __tablename__ = "owner"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    iban = Column(String, unique=True)

    @staticmethod
    async def create_owner(db: AsyncSession, username: str, iban: str):
        query = select(Owner).where(Owner.iban == iban)
        result = await db.execute(query)
        existing_owner = result.scalar_one_or_none()

        if existing_owner:
            return existing_owner

        new_owner = Owner(username=username, iban=iban)
        db.add(new_owner)
        await db.commit()
        await db.refresh(new_owner)

        return new_owner


class Transactions(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    from_account = Column(String)
    to_account = Column(String)
    status = Column(String)
    amount = Column(Integer)

    async def success(self, db):
        self.status = "success"
        db.add(self)
        await db.commit()

    async def cancel(self, db):
        self.status = "cancel"
        db.add(self)
        await db.commit()

    @staticmethod
    async def get_by_id(db, id_transaction: int):
        owner_query = select(Transactions).where(Transactions.id == id_transaction)
        result = await db.execute(owner_query)
        return result.scalar_one_or_none()


    @staticmethod
    async def create_transaction(
            db: AsyncSession,
            current_username: str,
            from_account: str,
            to_account: str,
            amount: int  # Очікуємо вже ціле число (копійки)
    ):
        # 1. Перевіряємо, чи належить рахунок відправника поточному користувачу
        owner_query = select(Owner).where(
            Owner.iban == from_account,
            Owner.username == current_username
        )
        result = await db.execute(owner_query)
        owner = result.scalar_one_or_none()

        if not owner and current_username != "CASH_DESK_SYSTEM":
            raise ValueError(f"Доступ заборонено: {current_username} не є власником рахунку {from_account}")

        # 2. Створюємо запис про транзакцію
        new_transaction = Transactions(
            from_account=from_account,
            to_account=to_account,
            amount=amount,
            status="pending"
        )

        db.add(new_transaction)
        await db.commit()
        await db.refresh(new_transaction)

        return new_transaction

    @staticmethod
    async def get_history(db: AsyncSession, iban: str, current_username: str):
        """
        Повертає історію транзакцій для конкретного рахунку від найстарішої до найновішої.
        - Відправник бачить всі свої транзакції (навіть скасовані).
        - Отримувач бачить тільки успішні або в обробці (скасовані приховуються).
        """

        owner_query = select(Owner).where(
            Owner.iban == iban,
            Owner.username == current_username
        )
        result = await db.execute(owner_query)
        owner = result.scalar_one_or_none()

        if not owner:
            raise ValueError(f"Доступ заборонено: {current_username} не є власником рахунку {iban}")

        query = select(Transactions).where(
            or_(
                # Умова 1: Ми відправник (беремо ВСІ транзакції)
                Transactions.from_account == iban,

                # Умова 2: Ми отримувач, але статус НЕ cancel (помилкові приховуємо)
                and_(
                    Transactions.to_account == iban,
                    Transactions.status != "cancel"
                )
            )
        ).order_by(Transactions.id.asc())  # asc() гарантує сортування від першого до останнього

        result = await db.execute(query)
        transactions = result.scalars().all()

        history_list = []

        for tx in transactions:
            # Визначаємо напрямок і знак суми
            if tx.from_account == iban:
                # Ми відправляли гроші -> сума з мінусом
                direction = "out"
                signed_amount = -tx.amount
                counterparty = tx.to_account  # Інша сторона - це той, кому ми відправили
            else:
                # Ми отримували гроші -> сума з плюсом
                direction = "in"
                signed_amount = tx.amount
                counterparty = tx.from_account  # Інша сторона - це той, хто нам відправив

            history_list.append({
                "transaction_id": tx.id,
                "direction": direction,
                "counterparty": counterparty,  # З ким була операція
                "amount": signed_amount,  # Сума в копійках з правильним знаком (- або +)
                "status": tx.status
            })

        return history_list
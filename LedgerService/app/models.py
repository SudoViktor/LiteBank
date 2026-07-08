from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from sqlalchemy import select, or_, case


class History(Base):
    __tablename__ = "history"

    # Основні поля
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, index=True)  # Прив'язка до ID з Transaction Service
    type = Column(String)  # 'p2p' або 'cash_deposit'
    from_iban = Column(String, nullable=True)
    to_iban = Column(String, nullable=False)

    # (копійки/центи)
    amount = Column(Integer)


    status = Column(String)  # 'success', 'failed'
    initiator_user = Column(String)

    created_at = Column(DateTime, default=func.now())

    @staticmethod
    async def create_ledger_entry(
            db: AsyncSession,
            transaction_id: int,
            tx_type: str,
            to_account: str,
            amount: int,
            initiator_user: str,
            from_account: str = None
    ):
        """
        Універсальна функція для створення запису в історії Леджера.
        Обробляє як P2P перекази, так і поповнення готівкою.
        """

        # 1. Логіка для P2P (Peer-to-Peer) переказів
        if tx_type == "p2p":
            if not from_account:
                raise ValueError("A sender's account (from_account) is required for a P2P transfer.")

        # 2. Логіка для поповнення готівкою через касу/термінал
        elif tx_type == "cash_deposit":
            from_account = "CASH_DESK"

        else:
            raise ValueError(f"Unknown transaction type: {tx_type}")

        # Створюємо запис у базі
        new_entry = History(
            transaction_id=transaction_id,
            type=tx_type,
            from_iban=from_account,
            to_iban=to_account,
            amount=amount,
            initiator_user=initiator_user,
            status="success"
        )

        db.add(new_entry)
        await db.commit()
        await db.refresh(new_entry)

        return new_entry

    @staticmethod
    async def get_balance(db: AsyncSession, iban: str) -> int:  # ЗМІНЕНО: повертає int
        """
        Розраховує поточний баланс рахунку на основі всієї історії транзакцій.
        (Сума всіх надходжень) мінус (Сума всіх списань).
        """
        query = select(
            func.coalesce(
                # Додаємо гроші, якщо рахунок є отримувачем (to_iban)
                func.sum(
                    case(
                        (History.to_iban == iban, History.amount),
                        else_=0  # ЗМІНЕНО: 0 замість 0.0
                    )
                ) -
                # Віднімаємо гроші, якщо рахунок є відправником (from_iban)
                func.sum(
                    case(
                        (History.from_iban == iban, History.amount),
                        else_=0  # ЗМІНЕНО: 0 замість 0.0
                    )
                ),
                0  # ЗМІНЕНО: 0 замість 0.0
            )
        ).where(
            # Фільтруємо: беремо тільки ті рядки, де фігурує цей IBAN
            or_(History.to_iban == iban, History.from_iban == iban),
            # Обов'язково рахуємо тільки успішні транзакції
            History.status == "success"
        )

        result = await db.execute(query)
        balance = result.scalar()

        return balance or 0  # ЗМІНЕНО: 0 замість 0.0
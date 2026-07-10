import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_current_user
from app.models import Transactions
from app.kafka_produser import kafka_producer
from app.kafka_consumer import (
    KafkaConsumerRunner,
    process_account_event,
    process_completed_transaction
)
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запускаю фонові процеси Кафки...")

    account_runner = KafkaConsumerRunner(
        topic="AccountOwners",
        group_id="transaction_service_group",
        processor_func=process_account_event
    )

    complete_tx_runner = KafkaConsumerRunner(
        topic="CompleteTransaction",
        group_id="transaction_service_group",
        processor_func=process_completed_transaction
    )

    background_tasks = [
        asyncio.create_task(account_runner.start()),
        asyncio.create_task(complete_tx_runner.start())
    ]

    async with kafka_producer:
        yield  # 🟢 Сервер працює і приймає HTTP-запити

    logger.info("🛑 Вимикаю всі фонові процеси Кафки...")
    for task in background_tasks:
        task.cancel()

    await asyncio.gather(*background_tasks, return_exceptions=True)
    logger.info("✅ Всі процеси успішно зупинені.")


app = FastAPI(title="Transactions API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Сервер Transactions працює! 🚀"}


class TransactionInfo(BaseModel):
    type: str
    from_iban: str
    to_iban: str
    # Клієнт присилає звичайні дроби (напр. 15.50)
    amount: float


@app.post("/create_transaction")
async def create_transaction(
        transaction_info: TransactionInfo,
        current_user: str = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    # КОНВЕРТАЦІЯ: множимо на 100, округлюємо (щоб уникнути мікро-похибок float), і робимо цілим числом
    amount_in_cents = int(round(transaction_info.amount * 100))

    to_iban = transaction_info.to_iban
    if len(to_iban) == 16:
        to_iban =  transaction_info.to_iban

    try:
        transaction = await Transactions.create_transaction(
            db=db,
            current_username=current_user,
            from_account=transaction_info.from_iban,
            to_account=to_iban,
            amount=amount_in_cents  # Передаємо копійки у БД
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

    kafka_payload = {
        "transaction_id": transaction.id,
        "type": transaction_info.type,
        "from_account": transaction.from_account,
        "to_account": transaction.to_account,
        "amount": transaction.amount,
        "status": transaction.status,
        "initiator_user": current_user
    }
    await kafka_producer.send_event("CreateTransaction", kafka_payload)

    return {
        "message": "Транзакцію створено. Очікується обробка.",
        "transaction_id": transaction.id,
        "status": transaction.status,
        "requested_amount": transaction_info.amount,
        "kafka_event_data": kafka_payload
    }

@app.get("/history")
async def get_transaction_history(
    iban: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):

    history = await Transactions.get_history(db, iban, current_user)

    return {
        "message": "Історія транзакцій успішно завантажена",
        "iban": iban,
        "total_records": len(history),
        "transactions": history
    }
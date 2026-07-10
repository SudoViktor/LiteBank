import asyncio

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
import logging
from contextlib import asynccontextmanager
from app.kafka_consumer import consume_tranche_events
from app.kafka_producer import kafka_producer
from app.models import History
from fastapi.middleware.cors import CORSMiddleware
logger = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запускаю фоновий процес Кафки...")
    consumer_task = asyncio.create_task(consume_tranche_events())

    async with kafka_producer:
        yield  # Сервер працює і приймає запити

    logger.info("🛑 Зупиняю фоновий процес Кафки...")
    consumer_task.cancel()


app = FastAPI(title="Ledger API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Сервер Ledger працює! 🚀"}


@app.get("/balance")
async def get_account_balance(iban: str, db: AsyncSession = Depends(get_db)):
    balance_in_cents = await History.get_balance(db, iban)

    display_balance = balance_in_cents / 100.0

    return {
        "iban": iban, 
        "balance": display_balance,
        "balance_in_cents": balance_in_cents
    }
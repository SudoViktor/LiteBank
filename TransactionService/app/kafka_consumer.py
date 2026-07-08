import json
import os
import asyncio
import logging
from typing import Callable, Awaitable
from aiokafka import AIOKafkaConsumer

from app.models import Owner
from app.database import AsyncSessionLocal
from app.models import Transactions

logger = logging.getLogger("uvicorn")

class KafkaConsumerRunner:
    """
    Універсальний клас для створення Kafka-консюмерів.
    """
    def __init__(
        self,
        topic: str,
        group_id: str,
        processor_func: Callable[[dict], Awaitable[bool]]
    ):
        self.topic = topic
        self.group_id = group_id
        self.processor_func = processor_func
        self.kafka_url = os.getenv("KAFKA_URL", "localhost:9094")
        self.consumer = None

    async def start(self):
        """
        Головний цикл, який запускається як фонова задача у FastAPI.
        """
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.kafka_url,
            group_id=self.group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            enable_auto_commit=False,
            auto_offset_reset='earliest',
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000,
            max_poll_interval_ms=300000
        )

        await self.consumer.start()
        logger.info(f"🎧 Kafka Consumer для топіка '{self.topic}' успішно запущений.")

        try:
            async for msg in self.consumer:
                event_data = msg.value
                logger.info(f"📥 [{self.topic}] Отримано подію: {event_data}")

                # Викликаємо передану функцію бізнес-логіки
                is_success = await self.processor_func(event_data)

                # Комітимо тільки якщо обробка успішна (або дані биті)
                if is_success:
                    await self.consumer.commit()

        except asyncio.CancelledError:
            # Ця помилка виникає штатно, коли FastAPI вимикається і викликає task.cancel()
            logger.info(f"🛑 Отримано сигнал зупинки для консюмера '{self.topic}'...")
        except Exception as e:
            logger.error(f"❌ Критична помилка у консюмері '{self.topic}': {e}")
        finally:
            if self.consumer:
                await self.consumer.stop()
                logger.info(f"✅ Консюмер '{self.topic}' безпечно вимкнений.")


# --- БІЗНЕС-ЛОГІКА (Окремі функції для кожного топіка) ---

async def process_account_event(event_data: dict) -> bool:
    """Обробник для топіка AccountOwners"""
    username = event_data.get("user")
    iban = event_data.get("account")

    if not username or not iban:
        logger.warning("⚠️ Некоректний формат події, пропускаємо...")
        return True

    try:
        async with AsyncSessionLocal() as db:
            await Owner.create_owner(db, username=username, iban=iban)
            logger.info(f"✅ Власника збережено в БД: {username} -> {iban}")
        return True
    except Exception as db_error:
        logger.error(f"❌ Помилка БД: {db_error}")
        return False


# Приклад іншої функції для майбутнього топіка:
async def process_completed_transaction(event_data: dict) -> bool:
    tx_id = int(event_data.get('transaction_id'))
    status = event_data.get('status')
    try:
        async with AsyncSessionLocal() as db:

            transaction = await Transactions.get_by_id(db, tx_id)
            if status == "success":
                await transaction.success(db)
            else:
                await transaction.cancel(db)
        return True
    except Exception as db_error:
        logger.error(f"❌ Помилка БД: {db_error}")
        return False
    logger.info(f"Оновлюю статус транзакції {event_data.get('transaction_id')}")
    return True
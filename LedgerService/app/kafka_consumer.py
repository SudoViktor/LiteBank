import json
import os
import logging
from aiokafka import AIOKafkaConsumer
from app.models import History
from app.database import AsyncSessionLocal
from app.kafka_producer import kafka_producer

logger = logging.getLogger("uvicorn")

# --- CONSTANTS ---
KAFKA_URL = os.getenv("KAFKA_URL", "localhost:9092")
TOPIC_NAME = "CreateTransaction"
GROUP_ID = "ledger_processor_group"


def get_kafka_consumer() -> AIOKafkaConsumer:
    """
    Configures and returns the Kafka consumer instance.
    """
    return AIOKafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=KAFKA_URL,
        group_id=GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        enable_auto_commit=False,
        auto_offset_reset='earliest',
        session_timeout_ms=30000,
        heartbeat_interval_ms=10000,
        max_poll_interval_ms=300000
    )


async def process_tranche_event(event_data: dict) -> bool:


    try:
        async with AsyncSessionLocal() as db:
            await History.create_ledger_entry(
                db=db,
                transaction_id=event_data['transaction_id'],
                tx_type=event_data['type'],
                to_account=event_data['to_account'],
                amount=event_data['amount'],
                initiator_user=event_data['initiator_user'],
                from_account=event_data.get('from_account')
            )

            complete_payload = {
                "transaction_id": event_data['transaction_id'],
                "status": "success",
            }
            await kafka_producer.send_event("CompleteTransaction", complete_payload)
        return True

    except Exception as db_error:
        logger.error(f"❌ Database error: {db_error}")
        return False



async def consume_tranche_events():
    """
    Main background loop that listens for messages and orchestrates processing.
    """
    consumer = get_kafka_consumer()

    await consumer.start()
    logger.info("🎧 Kafka Consumer started. Waiting for new owners...")

    try:
        async for msg in consumer:
            event_data = msg.value
            logger.info(f"📥 Received event: {event_data}")

            # Pass the data to the business logic handler
            is_success = await process_tranche_event(event_data)

            # Commit ONLY if processing was successful or data was invalid
            if is_success:
                await consumer.commit()

    except Exception as e:
        logger.error(f"❌ Kafka Consumer error: {e}")
    finally:
        await consumer.stop()
        logger.info("🛑 Kafka Consumer gracefully stopped.")
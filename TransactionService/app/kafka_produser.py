import json
from aiokafka import AIOKafkaProducer
import os

class KafkaProducerClient:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def __aenter__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks="all"
        )
        await self.producer.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.producer:
            await self.producer.stop()
            print("🛑 Kafka Producer зупинено.")

    async def send_event(self, topic: str, data: dict):
        if not self.producer:
            raise RuntimeError("Kafka Producer не запущений!")

        await self.producer.send_and_wait(topic, data)

kafka_producer = KafkaProducerClient(os.getenv("KAFKA_URL"))
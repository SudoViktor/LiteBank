#!/bin/bash

echo "🚀 Starting of LiteBank..."

# 1. Запуск БД
echo "📂 Starting PostgreSQL..."
cd PostgreSQL && docker-compose up -d
echo "⏳ Waiting 15 seconds..."
sleep 15

# 2. Запуск Kafka
echo "📨 Starting Kafka..."
cd ../Kafka && docker-compose up -d
echo "⏳ Waiting 10 seconds..."
sleep 10

# 3. Запуск мікросервісів
echo "⚙️ Starting services..."
cd ../AuthService && docker-compose up -d
cd ../AccountService && docker-compose up -d
cd ../TransactionService && docker-compose up -d
cd ../LedgerService && docker-compose up -d

# 4. Запуск фронтенду
echo "🖥🖥 Frontend starting..."
cd ../Front && docker-compose up -d --build

echo "✅ System started! http://localhost:3000"
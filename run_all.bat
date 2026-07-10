@echo off
echo 🚀 Запуск LiteBank...

:: 1. Запуск БД
echo 📂 Запуск PostgreSQL...
cd PostgreSQL
docker-compose up -d
echo ⏳ Очікування 15 секунд...
timeout /t 15 /nobreak >nul

:: 2. Запуск Kafka
echo 📨 Запуск Kafka...
cd ..\Kafka
docker-compose up -d
echo ⏳ Очікування 10 секунд...
timeout /t 10 /nobreak >nul

:: 3. Запуск сервісів
echo ⚙️ Запуск сервісів...
cd ..\AuthService
docker-compose up -d

cd ..\AccountService
docker-compose up -d

cd ..\TransactionService
docker-compose up -d

cd ..\LedgerService
docker-compose up -d

:: 4. Запуск фронтенду
echo 🖥 Запуск фронтенду...
cd ..\Front
docker-compose up -d --build

echo ✅ Система запущена! http://localhost:3000
pause
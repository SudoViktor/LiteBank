FROM python:3.11-slim

WORKDIR /app

# Копіюємо залежності і встановлюємо їх
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код проєкту
COPY . .
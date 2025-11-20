FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание директории для статики
RUN mkdir -p /app/static

# Миграции выполняются при запуске через docker-compose
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

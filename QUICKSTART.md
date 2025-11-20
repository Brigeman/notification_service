# Быстрый старт

## Запуск через Docker Compose

```bash
# 1. ОБЯЗАТЕЛЬНО создайте .env файл (иначе docker-compose не запустится)
cp .env.example .env

# 2. Запустите все сервисы
docker-compose up --build

# Сервис будет доступен на http://localhost:8001
```

**Важно**: Без файла `.env` docker-compose выдаст ошибку. Убедитесь, что файл создан перед запуском.

## Локальный запуск

```bash
# 1. Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 2. Установите зависимости
pip install -r requirements.txt

# 3. Выполните миграции
python manage.py migrate

# 4. Запустите Redis (в отдельном терминале или через Docker)
docker run -d -p 6379:6379 redis:7-alpine

# 5. Запустите Django сервер
python manage.py runserver

# 6. В другом терминале запустите Celery worker
celery -A notification_service worker -l info
```

## Тестирование API

```bash
# Создание уведомления
curl -X POST http://localhost:8001/api/notifications/ \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@example.com",
    "body": "Test message",
    "channels": ["email", "sms"]
  }'

# Получение статуса (замените {id} на реальный ID из ответа)
curl http://localhost:8001/api/notifications/{id}/
```

## Запуск тестов

```bash
# Через pytest
pytest

# Через Django test runner
python manage.py test

# С подробным выводом
python manage.py test tests/ -v 2

# С покрытием кода (HTML отчет)
make test-coverage

# С покрытием кода (только терминал)
make test-coverage-term
```

**Результат**: 38 тестов, все проходят успешно ✅

**Покрытие кода**: ~88% (HTML отчет в `htmlcov/index.html`)

## Инструменты качества кода

```bash
# Установка pre-commit хуков
make pre-commit-install

# Проверка кода
make check

# Форматирование кода
make format
```

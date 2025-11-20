# Сервис уведомлений с fallback по каналам

Микросервис для отправки уведомлений пользователям через несколько каналов доставки (Email, SMS, Telegram) с автоматическим fallback при ошибках.

## Основные возможности

- ✅ **Fallback логика**: Автоматическое переключение между каналами при ошибках
- ✅ **Асинхронная обработка**: Celery для неблокирующей отправки уведомлений
- ✅ **Идемпотентность**: Защита от дубликатов через `request_id`
- ✅ **История попыток**: Полная история всех попыток доставки
- ✅ **Валидация**: Строгая валидация входных данных
- ✅ **Логирование**: Детальное логирование всех операций
- ✅ **Тестирование**: 38 тестов с полным покрытием основных сценариев

## Реализация

### Технологический стек

- **Framework**: Django 4.2.11
- **API**: Django REST Framework
- **База данных**: SQLite
- **Асинхронность**: Celery + Redis
- **Инструменты качества кода**: black, ruff, isort, mypy, pre-commit
- **Покрытие кода**: pytest-cov, coverage (~88%)

### Структура проекта

```
notification_service/
├── notification_service/     # Главный проект Django
│   ├── settings.py           # Настройки Django
│   ├── urls.py               # Главный URLconf
│   └── celery.py             # Конфигурация Celery
├── notifications/            # Django app для уведомлений
│   ├── models.py             # Notification, DeliveryAttempt
│   ├── serializers.py        # DRF Serializers
│   ├── views.py              # API Views
│   ├── tasks.py              # Celery задачи
│   ├── channels/             # Адаптеры каналов доставки
│   │   ├── base.py           # Базовый класс ChannelSender
│   │   ├── email_channel.py
│   │   ├── sms_channel.py
│   │   └── telegram_channel.py
│   └── services/             # Бизнес-логика
│       └── notification_service.py
├── tests/                    # Тесты
│   ├── test_api.py          # Тесты API endpoints
│   ├── test_channels.py     # Тесты каналов доставки
│   ├── test_services.py     # Тесты бизнес-логики
│   ├── test_serializers.py  # Тесты сериализаторов
│   ├── test_tasks.py        # Тесты Celery задач
│   ├── test_models.py       # Тесты моделей
│   └── test_edge_cases.py   # Тесты граничных случаев
├── docker-compose.yml        # Docker Compose конфигурация
├── Dockerfile                # Docker образ
├── .dockerignore            # Исключения для Docker
├── .pre-commit-config.yaml  # Конфигурация pre-commit
├── pyproject.toml           # Конфигурация инструментов качества кода
├── Makefile                 # Команды для разработки
└── requirements.txt          # Зависимости Python
```

### Установка и запуск

#### Вариант 1: Docker Compose (рекомендуется)

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd notification_service
```

2. **Обязательно** создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

   Или создайте файл `.env` вручную с содержимым:
```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=*
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8001
DJANGO_LOG_LEVEL=INFO
```

3. Запустите сервисы:
```bash
docker-compose up --build
```

Сервис будет доступен по адресу: http://localhost:8001

**Примечание**:
- При первом запуске Docker выполнит миграции базы данных автоматически.
- Если порты 6379 или 8000 уже заняты другими сервисами, docker-compose автоматически использует альтернативные порты:
  - Redis: внешний порт 6380 (внутри Docker сети - 6379)
  - Web: внешний порт 8001 (внутри Docker сети - 8000)

#### Вариант 2: Локальная установка

1. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Выполните миграции:
```bash
python manage.py migrate
```

4. Запустите Redis (требуется для Celery):
```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis

# Или через Docker
docker run -d -p 6379:6379 redis:7-alpine
```

5. В первом терминале запустите Django сервер:
```bash
python manage.py runserver
```

6. Во втором терминале запустите Celery worker:
```bash
celery -A notification_service worker -l info
```

### Использование Makefile

```bash
# Установка зависимостей
make install-dev

# Установка pre-commit хуков
make pre-commit-install

# Выполнение миграций
make migrate

# Запуск сервера
make runserver

# Запуск Celery worker
make celery

# Запуск тестов
make test

# Запуск тестов с покрытием кода (HTML отчет)
make test-coverage

# Запуск тестов с покрытием кода (терминал)
make test-coverage-term

# Форматирование кода
make format

# Проверка кода (lint + format check)
make check

# Очистка кэша и временных файлов
make clean
```

### Примеры запросов

#### 1. Создание уведомления

**POST** `/api/notifications/`

```bash
curl -X POST http://localhost:8001/api/notifications/ \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "user@example.com",
    "to_phone": "+49123456789",
    "to_telegram_chat_id": "123456789",
    "subject": "Test notification",
    "body": "Hello, this is a test",
    "channels": ["telegram", "email", "sms"]
  }'
```

**Ответ (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "used_channel": null
}
```

#### 2. Создание уведомления с идемпотентностью

**POST** `/api/notifications/` с `request_id`

```bash
curl -X POST http://localhost:8001/api/notifications/ \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "unique-request-id-123",
    "to_email": "user@example.com",
    "body": "Hello, this is a test"
  }'
```

При повторном запросе с тем же `request_id` вернется существующее уведомление (200 OK).

#### 3. Получение статуса уведомления

**GET** `/api/notifications/{id}/`

```bash
curl http://localhost:8001/api/notifications/550e8400-e29b-41d4-a716-446655440000/
```

**Ответ (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "delivered",
  "subject": "Test notification",
  "body": "Hello, this is a test",
  "to_email": "user@example.com",
  "to_phone": "+49123456789",
  "to_telegram_chat_id": "123456789",
  "channels": ["telegram", "email", "sms"],
  "used_channel": "email",
  "created_at": "2025-01-19T12:00:00Z",
  "updated_at": "2025-01-19T12:00:01Z",
  "attempts": [
    {
      "channel": "telegram",
      "status": "failed",
      "error_message": "Telegram Bot API timeout",
      "attempted_at": "2025-01-19T12:00:00Z"
    },
    {
      "channel": "email",
      "status": "success",
      "error_message": null,
      "attempted_at": "2025-01-19T12:00:01Z"
    }
  ]
}
```

#### 4. Пример с использованием httpie

```bash
# Создание уведомления
http POST http://localhost:8001/api/notifications/ \
  to_email=user@example.com \
  body="Test message" \
  channels:='["email","sms"]'

# Получение статуса
http GET http://localhost:8001/api/notifications/{notification_id}/
```

### Валидация запросов

API валидирует следующие требования:

- **Хотя бы один контакт**: должен быть указан `to_email`, `to_phone` или `to_telegram_chat_id`
- **Обязательное поле**: `body` обязателен
- **Валидные каналы**: `channels` может содержать только `["email", "sms", "telegram"]`

**Пример ошибки валидации:**

```bash
curl -X POST http://localhost:8001/api/notifications/ \
  -H "Content-Type: application/json" \
  -d '{"body": "Test"}'
```

**Ответ (400 Bad Request):**
```json
{
  "non_field_errors": [
    "At least one contact method must be provided (to_email, to_phone, or to_telegram_chat_id)"
  ]
}
```

### Логирование

Сервис логирует все попытки доставки в консоль:

```
INFO Attempting to send email to user@example.com for notification 550e8400-...
INFO Email sent successfully to user@example.com for notification 550e8400-...
INFO Notification 550e8400-... delivered successfully via email
```

При ошибках:
```
WARNING Channel telegram unavailable: No Telegram chat ID provided
ERROR SMS send failed: SMS provider API error
ERROR All channels failed for notification 550e8400-..., marking as failed
```

### Тестирование

Запуск тестов:
```bash
# Через pytest
pytest

# Через Django test runner
python manage.py test

# С покрытием кода (HTML отчет)
make test-coverage
# или
pytest --cov=notifications --cov-report=html --cov-report=term-missing

# С покрытием кода (только терминал)
make test-coverage-term
# или
pytest --cov=notifications --cov-report=term-missing
```

**Текущее покрытие кода**: ~88% (288 строк кода, 35 непокрытых)

HTML отчет доступен в `htmlcov/index.html` после запуска с coverage.

Тесты покрывают (38 тестов):

**API тесты (6 тестов):**
- Успешное создание уведомления
- Валидация входных данных (нет контактов, невалидный канал)
- Идемпотентность через `request_id`
- Получение деталей уведомления
- Обработка 404 для несуществующего уведомления

**Тесты каналов (3 теста):**
- Доступность каждого канала (email, SMS, Telegram)

**Тесты сервиса (4 теста):**
- Fallback логику (первый канал падает → второй успешен)
- Случай, когда все каналы падают → статус `failed`
- Пропуск недоступных каналов
- Использование дефолтных каналов

**Тесты сериализаторов (7 тестов):**
- Валидация всех полей
- Обязательные и опциональные поля
- Валидность каналов

**Тесты Celery задач (3 теста):**
- Успешное выполнение задачи
- Обработка несуществующего уведомления
- Обработка исключений

**Тесты моделей (8 тестов):**
- Создание и валидация моделей
- Связи между моделями
- Уникальность `request_id`

**Тесты граничных случаев (7 тестов):**
- Неизвестные каналы в списке
- Все каналы недоступны
- Пустое тело сообщения
- Очень длинные сообщения
- Один канал в списке

### Инструменты качества кода

Проект использует следующие инструменты:

- **black** - форматирование кода
- **ruff** - линтер
- **isort** - сортировка импортов
- **mypy** - проверка типов
- **pre-commit** - хуки для проверки перед коммитом
- **pytest-cov** - измерение покрытия кода тестами
- **coverage** - генерация отчетов о покрытии

Установка pre-commit хуков:
```bash
make pre-commit-install
```

Проверка кода:
```bash
make check
```

Форматирование кода:
```bash
make format
```

Проверка покрытия кода:
```bash
# HTML отчет
make test-coverage

# Терминальный отчет
make test-coverage-term
```

**Текущее покрытие**: ~88% (288 строк кода, 35 непокрытых строк)

### Архитектурные решения

1. **Fallback логика**: Последовательный перебор каналов с остановкой при первом успехе
2. **Асинхронность**: Celery задачи для неблокирующей отправки уведомлений
3. **Идемпотентность**: Проверка `request_id` перед созданием уведомления
4. **Расширяемость**: Легко добавить новые каналы через наследование от `ChannelSender`
5. **Логирование**: Структурированные логи всех попыток доставки
6. **Тестируемость**: Изолированные компоненты с моками для тестирования

### Админка Django

Доступ к админке: http://localhost:8001/admin/

Создание суперпользователя:
```bash
python manage.py createsuperuser
```

### Статистика проекта

- **Python файлов**: 29
- **Тестов**: 38 (100% прохождение)
- **Покрытие кода**: ~88% (288 строк кода, 35 непокрытых)
- **Каналов доставки**: 3 (email, SMS, Telegram)
- **API endpoints**: 2 (POST /notifications/, GET /notifications/{id}/)
- **Покрытие тестами**: Все основные сценарии и граничные случаи

### Дополнительные возможности

- **API Key аутентификация**: Можно добавить через middleware (описано в архитектуре)
- **Метрики**: Можно интегрировать Prometheus/Grafana
- **Retry логика**: Можно добавить повторные попытки для failed каналов
- **Webhooks**: Можно добавить уведомления о статусе доставки
- **Rate limiting**: Можно добавить ограничение частоты запросов
- **Мониторинг**: Можно интегрировать Sentry для отслеживания ошибок

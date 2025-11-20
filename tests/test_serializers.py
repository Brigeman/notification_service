from django.test import TestCase

from notifications.serializers import NotificationCreateSerializer


class NotificationCreateSerializerTest(TestCase):
    """Тесты для сериализатора создания уведомления."""

    def test_valid_data(self):
        """Тест валидных данных."""
        data = {
            "to_email": "test@example.com",
            "body": "Test message",
            "channels": ["email"],
        }
        serializer = NotificationCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_missing_body(self):
        """Тест: отсутствует обязательное поле body."""
        data = {
            "to_email": "test@example.com",
        }
        serializer = NotificationCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("body", serializer.errors)

    def test_no_contacts(self):
        """Тест: нет ни одного контакта."""
        data = {
            "body": "Test message",
        }
        serializer = NotificationCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_invalid_channel(self):
        """Тест: невалидный канал."""
        data = {
            "to_email": "test@example.com",
            "body": "Test message",
            "channels": ["invalid"],
        }
        serializer = NotificationCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("channels", serializer.errors)

    def test_empty_channels_list(self):
        """Тест: пустой список каналов не валиден (allow_empty=False)."""
        data = {
            "to_email": "test@example.com",
            "body": "Test message",
            "channels": [],
        }
        serializer = NotificationCreateSerializer(data=data)
        # Пустой список не валиден согласно настройкам сериализатора
        self.assertFalse(serializer.is_valid())
        self.assertIn("channels", serializer.errors)

    def test_multiple_contacts(self):
        """Тест: несколько контактов одновременно."""
        data = {
            "to_email": "test@example.com",
            "to_phone": "+1234567890",
            "to_telegram_chat_id": "123456789",
            "body": "Test message",
        }
        serializer = NotificationCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_request_id_optional(self):
        """Тест: request_id опционален."""
        data = {
            "to_email": "test@example.com",
            "body": "Test message",
        }
        serializer = NotificationCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

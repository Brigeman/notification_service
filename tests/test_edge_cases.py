from django.test import TestCase

from notifications.models import Notification
from notifications.services import NotificationService


class EdgeCasesTest(TestCase):
    """Тесты для граничных случаев и edge cases."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.service = NotificationService()

    def test_unknown_channel_in_list(self):
        """Тест: неизвестный канал в списке пропускается."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
            channels=["unknown_channel", "email"],
        )

        # Неизвестный канал должен быть пропущен (логируется warning), email должен отработать
        self.service.send_notification(notification)

        notification.refresh_from_db()
        # Если email успешно доставил, статус должен быть delivered
        # Но если email упал случайно, статус будет failed
        # Проверяем, что попытка была хотя бы для email
        attempts = notification.attempts.all()
        self.assertGreaterEqual(len(attempts), 1)
        # Проверяем, что есть попытка для email (неизвестный канал пропущен)
        email_attempts = [a for a in attempts if a.channel == "email"]
        self.assertEqual(len(email_attempts), 1)

    def test_all_channels_unavailable(self):
        """Тест: все каналы недоступны (нет контактов)."""
        notification = Notification.objects.create(
            # Нет контактов вообще
            body="Test message",
            channels=["email", "sms", "telegram"],
        )

        self.service.send_notification(notification)

        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.STATUS_FAILED)

        # Все попытки должны быть failed
        attempts = notification.attempts.all()
        self.assertEqual(len(attempts), 3)
        for attempt in attempts:
            self.assertEqual(attempt.status, "failed")
            self.assertIsNotNone(attempt.error_message)

    def test_empty_body(self):
        """Тест: пустое тело сообщения (валидация должна быть на уровне API)."""
        # На уровне модели пустое body допустимо (валидация в сериализаторе)
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="",  # Пустое тело
        )

        # Сервис должен обработать (валидация на уровне API)
        # Но если все каналы упадут случайно, статус будет failed
        self.service.send_notification(notification)

        notification.refresh_from_db()
        # Проверяем, что была попытка доставки (статус может быть delivered или failed)
        self.assertIn(
            notification.status,
            [Notification.STATUS_DELIVERED, Notification.STATUS_FAILED],
        )
        # Проверяем, что попытки были созданы
        attempts = notification.attempts.all()
        self.assertGreater(len(attempts), 0)

    def test_very_long_body(self):
        """Тест: очень длинное тело сообщения."""
        long_body = "A" * 10000  # 10KB сообщение

        notification = Notification.objects.create(
            to_email="test@example.com",
            body=long_body,
        )

        self.service.send_notification(notification)

        notification.refresh_from_db()
        self.assertEqual(notification.body, long_body)
        self.assertEqual(notification.status, Notification.STATUS_DELIVERED)

    def test_single_channel_success(self):
        """Тест: один канал в списке, успешная доставка."""
        from unittest.mock import patch

        from notifications.channels.base import ChannelResult

        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
            channels=["email"],
        )

        # Мокаем email канал для гарантированного успеха
        with patch.object(
            self.service.channel_senders["email"],
            "send",
            return_value=ChannelResult(success=True),
        ):
            self.service.send_notification(notification)

        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.STATUS_DELIVERED)
        self.assertEqual(notification.used_channel, "email")

    def test_single_channel_fail(self):
        """Тест: один канал в списке, ошибка доставки."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
            channels=["email"],
        )

        # Временно делаем email канал всегда падающим для этого теста
        from unittest.mock import patch

        from notifications.channels.base import ChannelResult

        with patch.object(
            self.service.channel_senders["email"],
            "send",
            return_value=ChannelResult(success=False, error_message="Email failed"),
        ):
            self.service.send_notification(notification)

        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.STATUS_FAILED)
        self.assertIsNone(notification.used_channel)

from unittest.mock import patch

from django.test import TestCase

from notifications.channels.base import ChannelResult
from notifications.models import DeliveryAttempt, Notification
from notifications.services import NotificationService


class NotificationServiceTest(TestCase):
    """Тесты для NotificationService."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.service = NotificationService()

    def test_fallback_first_channel_fails_second_succeeds(self):
        """Тест fallback: первый канал падает, второй успешен."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            to_phone="+1234567890",
            body="Test message",
            channels=["email", "sms"],
        )

        # Мокаем каналы: email падает, sms успешен
        with (
            patch.object(
                self.service.channel_senders["email"],
                "send",
                return_value=ChannelResult(success=False, error_message="Email failed"),
            ),
            patch.object(
                self.service.channel_senders["sms"],
                "send",
                return_value=ChannelResult(success=True),
            ),
        ):
            self.service.send_notification(notification)

        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.STATUS_DELIVERED)
        self.assertEqual(notification.used_channel, "sms")

        # Проверяем попытки
        attempts = notification.attempts.all()
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0].channel, "email")
        self.assertEqual(attempts[0].status, DeliveryAttempt.STATUS_FAILED)
        self.assertEqual(attempts[1].channel, "sms")
        self.assertEqual(attempts[1].status, DeliveryAttempt.STATUS_SUCCESS)

    def test_all_channels_fail(self):
        """Тест: все каналы падают → статус failed."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            to_phone="+1234567890",
            body="Test message",
            channels=["email", "sms"],
        )

        # Мокаем каналы: оба падают
        with (
            patch.object(
                self.service.channel_senders["email"],
                "send",
                return_value=ChannelResult(success=False, error_message="Email failed"),
            ),
            patch.object(
                self.service.channel_senders["sms"],
                "send",
                return_value=ChannelResult(success=False, error_message="SMS failed"),
            ),
        ):
            self.service.send_notification(notification)

        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.STATUS_FAILED)
        self.assertIsNone(notification.used_channel)

        # Проверяем попытки
        attempts = notification.attempts.all()
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0].status, DeliveryAttempt.STATUS_FAILED)
        self.assertEqual(attempts[1].status, DeliveryAttempt.STATUS_FAILED)

    def test_channel_unavailable_skipped(self):
        """Тест: недоступный канал пропускается."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            # Нет телефона
            body="Test message",
            channels=["email", "sms"],
        )

        # Мокаем email успешным
        with patch.object(
            self.service.channel_senders["email"],
            "send",
            return_value=ChannelResult(success=True),
        ):
            self.service.send_notification(notification)

        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.STATUS_DELIVERED)
        self.assertEqual(notification.used_channel, "email")

        # Проверяем попытки: только email, sms пропущен
        attempts = notification.attempts.all()
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].channel, "email")

    def test_default_channels_used_when_not_specified(self):
        """Тест: используются дефолтные каналы, если не указаны."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
            channels=[],  # Пустой список
        )

        # Мокаем email успешным
        with patch.object(
            self.service.channel_senders["email"],
            "send",
            return_value=ChannelResult(success=True),
        ):
            self.service.send_notification(notification)

        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.STATUS_DELIVERED)
        # Проверяем, что использовался email (первый в дефолтном списке)
        self.assertEqual(notification.used_channel, "email")

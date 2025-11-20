from django.test import TestCase

from notifications.channels.email_channel import EmailChannelSender
from notifications.channels.sms_channel import SmsChannelSender
from notifications.channels.telegram_channel import TelegramChannelSender
from notifications.models import Notification


class ChannelSenderTest(TestCase):
    """Тесты для каналов доставки."""

    def test_email_channel_availability(self):
        """Тест доступности email канала."""
        sender = EmailChannelSender()

        # С email - доступен
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test",
        )
        self.assertTrue(sender.is_available(notification))

        # Без email - недоступен
        notification.to_email = None
        notification.save()
        self.assertFalse(sender.is_available(notification))

    def test_sms_channel_availability(self):
        """Тест доступности SMS канала."""
        sender = SmsChannelSender()

        # С телефоном - доступен
        notification = Notification.objects.create(
            to_phone="+1234567890",
            body="Test",
        )
        self.assertTrue(sender.is_available(notification))

        # Без телефона - недоступен
        notification.to_phone = None
        notification.save()
        self.assertFalse(sender.is_available(notification))

    def test_telegram_channel_availability(self):
        """Тест доступности Telegram канала."""
        sender = TelegramChannelSender()

        # С chat_id - доступен
        notification = Notification.objects.create(
            to_telegram_chat_id="123456789",
            body="Test",
        )
        self.assertTrue(sender.is_available(notification))

        # Без chat_id - недоступен
        notification.to_telegram_chat_id = None
        notification.save()
        self.assertFalse(sender.is_available(notification))

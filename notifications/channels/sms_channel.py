import logging
import random

from notifications.channels.base import ChannelResult, ChannelSender
from notifications.models import Notification

logger = logging.getLogger(__name__)


class SmsChannelSender(ChannelSender):
    """Канал отправки уведомлений через SMS."""

    def is_available(self, notification: Notification) -> bool:
        """Проверяет наличие номера телефона."""
        return bool(notification.to_phone)

    def get_unavailable_reason(self, notification: Notification) -> str:
        """Возвращает причину недоступности SMS канала."""
        if not notification.to_phone:
            return "No phone number provided"
        return super().get_unavailable_reason(notification)

    def send(self, notification: Notification) -> ChannelResult:
        """
        Имитирует отправку SMS.

        Для демонстрации fallback иногда эмулирует ошибки.
        """
        if not self.is_available(notification):
            reason = self.get_unavailable_reason(notification)
            logger.warning(f"SMS channel unavailable: {reason}")
            return ChannelResult(success=False, error_message=reason)

        logger.info(
            f"Attempting to send SMS to {notification.to_phone} "
            f"for notification {notification.id}",
        )

        # Имитация отправки SMS
        # Для демонстрации fallback: 25% вероятность ошибки
        if random.random() < 0.25:
            error_msg = "SMS provider API error"
            logger.error(f"SMS send failed: {error_msg}")
            return ChannelResult(success=False, error_message=error_msg)

        # Успешная отправка
        logger.info(
            f"SMS sent successfully to {notification.to_phone} "
            f"for notification {notification.id}",
        )
        return ChannelResult(success=True)

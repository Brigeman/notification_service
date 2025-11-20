import logging
import random

from notifications.channels.base import ChannelResult, ChannelSender
from notifications.models import Notification

logger = logging.getLogger(__name__)


class EmailChannelSender(ChannelSender):
    """Канал отправки уведомлений через Email."""

    def is_available(self, notification: Notification) -> bool:
        """Проверяет наличие email адреса."""
        return bool(notification.to_email)

    def get_unavailable_reason(self, notification: Notification) -> str:
        """Возвращает причину недоступности email канала."""
        if not notification.to_email:
            return "No email address provided"
        return super().get_unavailable_reason(notification)

    def send(self, notification: Notification) -> ChannelResult:
        """
        Имитирует отправку email.

        Для демонстрации fallback иногда эмулирует ошибки.
        """
        if not self.is_available(notification):
            reason = self.get_unavailable_reason(notification)
            logger.warning(f"Email channel unavailable: {reason}")
            return ChannelResult(success=False, error_message=reason)

        logger.info(
            f"Attempting to send email to {notification.to_email} "
            f"for notification {notification.id}",
        )

        # Имитация отправки email
        # Для демонстрации fallback: 20% вероятность ошибки
        if random.random() < 0.2:
            error_msg = "Email service temporarily unavailable"
            logger.error(f"Email send failed: {error_msg}")
            return ChannelResult(success=False, error_message=error_msg)

        # Успешная отправка
        logger.info(
            f"Email sent successfully to {notification.to_email} "
            f"for notification {notification.id}",
        )
        return ChannelResult(success=True)

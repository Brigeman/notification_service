import logging
import random

from notifications.channels.base import ChannelResult, ChannelSender
from notifications.models import Notification

logger = logging.getLogger(__name__)


class TelegramChannelSender(ChannelSender):
    """Канал отправки уведомлений через Telegram."""

    def is_available(self, notification: Notification) -> bool:
        """Проверяет наличие Telegram chat ID."""
        return bool(notification.to_telegram_chat_id)

    def get_unavailable_reason(self, notification: Notification) -> str:
        """Возвращает причину недоступности Telegram канала."""
        if not notification.to_telegram_chat_id:
            return "No Telegram chat ID provided"
        return super().get_unavailable_reason(notification)

    def send(self, notification: Notification) -> ChannelResult:
        """
        Имитирует отправку сообщения в Telegram.

        Для демонстрации fallback иногда эмулирует ошибки.
        """
        if not self.is_available(notification):
            reason = self.get_unavailable_reason(notification)
            logger.warning(f"Telegram channel unavailable: {reason}")
            return ChannelResult(success=False, error_message=reason)

        logger.info(
            f"Attempting to send Telegram message to {notification.to_telegram_chat_id} "
            f"for notification {notification.id}",
        )

        # Имитация отправки через Telegram Bot API
        # Для демонстрации fallback: 30% вероятность ошибки
        if random.random() < 0.3:
            error_msg = "Telegram Bot API timeout"
            logger.error(f"Telegram send failed: {error_msg}")
            return ChannelResult(success=False, error_message=error_msg)

        # Успешная отправка
        logger.info(
            f"Telegram message sent successfully to {notification.to_telegram_chat_id} "
            f"for notification {notification.id}",
        )
        return ChannelResult(success=True)

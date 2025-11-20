import logging

from django.db import transaction

from notifications.channels import EmailChannelSender, SmsChannelSender, TelegramChannelSender
from notifications.models import DeliveryAttempt, Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений с fallback по каналам."""

    DEFAULT_CHANNELS = ["email", "sms", "telegram"]

    def __init__(self):
        """Инициализирует сервис с адаптерами каналов."""
        self.channel_senders = {
            "email": EmailChannelSender(),
            "sms": SmsChannelSender(),
            "telegram": TelegramChannelSender(),
        }

    def send_notification(self, notification: Notification) -> None:
        """
        Отправляет уведомление с fallback по каналам.

        Логика работы:
        1. Устанавливает статус in_progress
        2. Получает список каналов (из notification.channels или дефолтный)
        3. Для каждого канала последовательно:
           - Проверяет доступность
           - Если недоступен → создает failed attempt, переходит дальше
           - Пытается отправить
           - Если success → создает success attempt, статус=delivered, выходит
           - Если failed → создает failed attempt, переходит к следующему
        4. Если все каналы провалились → статус=failed

        Args:
            notification: Уведомление для отправки
        """
        logger.info(f"Starting notification delivery for {notification.id}")

        # Обновляем статус на in_progress
        notification.status = Notification.STATUS_IN_PROGRESS
        notification.save(update_fields=["status"])

        # Получаем список каналов
        channels = notification.channels if notification.channels else self.DEFAULT_CHANNELS
        logger.info(f"Channels to try: {channels}")

        # Пробуем каждый канал последовательно
        for channel_name in channels:
            if channel_name not in self.channel_senders:
                logger.warning(f"Unknown channel: {channel_name}, skipping")
                continue

            channel_sender = self.channel_senders[channel_name]
            logger.info(f"Attempting channel: {channel_name}")

            # Проверяем доступность канала
            if not channel_sender.is_available(notification):
                reason = channel_sender.get_unavailable_reason(notification)
                logger.warning(f"Channel {channel_name} unavailable: {reason}")
                self._create_attempt(
                    notification=notification,
                    channel=channel_name,
                    success=False,
                    error_message=reason,
                )
                continue

            # Пытаемся отправить
            result = channel_sender.send(notification)

            # Создаем запись о попытке
            self._create_attempt(
                notification=notification,
                channel=channel_name,
                success=result.success,
                error_message=result.error_message,
            )

            # Если успешно - завершаем
            if result.success:
                logger.info(
                    f"Notification {notification.id} delivered successfully via {channel_name}",
                )
                with transaction.atomic():
                    notification.status = Notification.STATUS_DELIVERED
                    notification.used_channel = channel_name
                    notification.save(update_fields=["status", "used_channel"])
                return

            # Если не успешно - продолжаем со следующим каналом
            logger.warning(
                f"Channel {channel_name} failed for notification {notification.id}, "
                f"trying next channel",
            )

        # Все каналы провалились
        logger.error(
            f"All channels failed for notification {notification.id}, " f"marking as failed",
        )
        notification.status = Notification.STATUS_FAILED
        notification.save(update_fields=["status"])

    def _create_attempt(
        self,
        notification: Notification,
        channel: str,
        success: bool,
        error_message: str | None = None,
    ) -> DeliveryAttempt:
        """
        Создает запись о попытке доставки.

        Args:
            notification: Уведомление
            channel: Название канала
            success: Успешна ли попытка
            error_message: Сообщение об ошибке (если есть)

        Returns:
            Созданная запись DeliveryAttempt
        """
        status = DeliveryAttempt.STATUS_SUCCESS if success else DeliveryAttempt.STATUS_FAILED
        attempt = DeliveryAttempt.objects.create(
            notification=notification,
            channel=channel,
            status=status,
            error_message=error_message,
        )
        logger.debug(
            f"Created delivery attempt: {attempt.id} for notification {notification.id} "
            f"via {channel} - {status}",
        )
        return attempt

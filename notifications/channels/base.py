import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from notifications.models import Notification

logger = logging.getLogger(__name__)


@dataclass
class ChannelResult:
    """Результат попытки отправки через канал."""

    success: bool
    error_message: str | None = None

    def __str__(self) -> str:
        if self.success:
            return "Success"
        return f"Failed: {self.error_message}"


class ChannelSender(ABC):
    """Базовый класс для отправки уведомлений через канал."""

    @abstractmethod
    def is_available(self, notification: Notification) -> bool:
        """
        Проверяет, доступен ли канал для данного уведомления.

        Args:
            notification: Уведомление для проверки

        Returns:
            True если канал доступен, False иначе
        """
        pass

    @abstractmethod
    def send(self, notification: Notification) -> ChannelResult:
        """
        Отправляет уведомление через канал.

        Args:
            notification: Уведомление для отправки

        Returns:
            ChannelResult с результатом отправки
        """
        pass

    def get_unavailable_reason(self, notification: Notification) -> str:
        """
        Возвращает причину недоступности канала.

        Args:
            notification: Уведомление для проверки

        Returns:
            Строка с описанием причины недоступности
        """
        return f"Channel {self.__class__.__name__} is not available"

import logging

from celery import shared_task

from notifications.models import Notification
from notifications.services import NotificationService

logger = logging.getLogger(__name__)


@shared_task
def send_notification_task(notification_id: str) -> None:
    """
    Асинхронная задача для отправки уведомления.

    Args:
        notification_id: UUID уведомления
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        logger.info(f"Processing notification {notification_id} in Celery task")
        service = NotificationService()
        service.send_notification(notification)
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error processing notification {notification_id}: {e}", exc_info=True)
        # Обновляем статус на failed при неожиданной ошибке
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.status = Notification.STATUS_FAILED
            notification.save(update_fields=["status"])
        except Notification.DoesNotExist:
            pass
        raise

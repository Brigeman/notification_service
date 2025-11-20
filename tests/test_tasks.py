from unittest.mock import patch

from django.test import TestCase

from notifications.models import Notification
from notifications.tasks import send_notification_task


class CeleryTasksTest(TestCase):
    """Тесты для Celery задач."""

    @patch("notifications.tasks.NotificationService")
    def test_send_notification_task_success(self, mock_service_class):
        """Тест успешного выполнения задачи отправки."""
        # Создаем уведомление
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
            status=Notification.STATUS_PENDING,
        )

        # Мокаем сервис
        mock_service = mock_service_class.return_value
        mock_service.send_notification.return_value = None

        # Вызываем задачу
        send_notification_task(str(notification.id))

        # Проверяем, что сервис был вызван
        mock_service.send_notification.assert_called_once_with(notification)

    def test_send_notification_task_not_found(self):
        """Тест: уведомление не найдено."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        # Должно поднять исключение
        with self.assertRaises(Notification.DoesNotExist):
            send_notification_task(fake_id)

    @patch("notifications.tasks.NotificationService")
    def test_send_notification_task_exception_handling(self, mock_service_class):
        """Тест обработки исключений в задаче."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
            status=Notification.STATUS_PENDING,
        )

        # Мокаем сервис, чтобы он выбрасывал исключение
        mock_service = mock_service_class.return_value
        mock_service.send_notification.side_effect = Exception("Test error")

        # Вызываем задачу - должно поднять исключение
        with self.assertRaises(Exception):  # noqa: B017
            send_notification_task(str(notification.id))

        # Проверяем, что статус обновлен на failed
        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.STATUS_FAILED)

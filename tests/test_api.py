import json
import uuid

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from notifications.models import Notification


class NotificationAPITest(TestCase):
    """Тесты для API endpoints."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.client = APIClient()

    def test_create_notification_success(self):
        """Тест успешного создания уведомления."""
        url = reverse("notifications:create")
        data = {
            "to_email": "test@example.com",
            "body": "Test message",
            "channels": ["email"],
        }

        response = self.client.post(url, data=json.dumps(data), content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Notification.STATUS_PENDING)

        # Проверяем, что уведомление создано
        notification = Notification.objects.get(id=response.data["id"])
        self.assertEqual(notification.to_email, "test@example.com")
        self.assertEqual(notification.body, "Test message")

    def test_create_notification_validation_no_contacts(self):
        """Тест валидации: нет контактов."""
        url = reverse("notifications:create")
        data = {
            "body": "Test message",
        }

        response = self.client.post(url, data=json.dumps(data), content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("contact", str(response.data).lower())

    def test_create_notification_validation_invalid_channel(self):
        """Тест валидации: невалидный канал."""
        url = reverse("notifications:create")
        data = {
            "to_email": "test@example.com",
            "body": "Test message",
            "channels": ["invalid_channel"],
        }

        response = self.client.post(url, data=json.dumps(data), content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_idempotency_same_request_id(self):
        """Тест идемпотентности: одинаковый request_id."""
        url = reverse("notifications:create")
        request_id = str(uuid.uuid4())
        data = {
            "request_id": request_id,
            "to_email": "test@example.com",
            "body": "Test message",
        }

        # Первый запрос
        response1 = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        notification_id = response1.data["id"]

        # Второй запрос с тем же request_id
        response2 = self.client.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        # Должен вернуть то же уведомление
        self.assertEqual(response2.data["id"], notification_id)

        # Проверяем, что создано только одно уведомление
        self.assertEqual(Notification.objects.filter(request_id=request_id).count(), 1)

    def test_get_notification_detail(self):
        """Тест получения детальной информации об уведомлении."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
            status=Notification.STATUS_DELIVERED,
            used_channel="email",
        )

        url = reverse("notifications:detail", kwargs={"notification_id": notification.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(notification.id))
        self.assertEqual(response.data["status"], Notification.STATUS_DELIVERED)
        self.assertEqual(response.data["body"], "Test message")
        self.assertIn("attempts", response.data)

    def test_get_notification_not_found(self):
        """Тест получения несуществующего уведомления."""
        fake_id = uuid.uuid4()
        url = reverse("notifications:detail", kwargs={"notification_id": fake_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

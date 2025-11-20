from django.test import TestCase

from notifications.models import DeliveryAttempt, Notification


class NotificationModelTest(TestCase):
    """Тесты для модели Notification."""

    def test_create_notification(self):
        """Тест создания уведомления."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
            channels=["email", "sms"],
        )

        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.status, Notification.STATUS_PENDING)
        self.assertEqual(notification.to_email, "test@example.com")
        self.assertEqual(notification.body, "Test message")
        self.assertEqual(notification.channels, ["email", "sms"])

    def test_notification_str(self):
        """Тест строкового представления."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
            status=Notification.STATUS_DELIVERED,
        )

        str_repr = str(notification)
        self.assertIn(str(notification.id), str_repr)
        self.assertIn(Notification.STATUS_DELIVERED, str_repr)

    def test_notification_default_channels(self):
        """Тест дефолтных каналов."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
            channels=[],
        )

        self.assertEqual(notification.channels, [])

    def test_notification_with_request_id(self):
        """Тест создания с request_id."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
            request_id="test-request-123",
        )

        self.assertEqual(notification.request_id, "test-request-123")

    def test_notification_unique_request_id(self):
        """Тест уникальности request_id."""
        Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
            request_id="test-request-123",
        )

        # Попытка создать второе уведомление с тем же request_id должна вызвать ошибку
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Notification.objects.create(
                to_email="test2@example.com",
                body="Test message 2",
                request_id="test-request-123",
            )


class DeliveryAttemptModelTest(TestCase):
    """Тесты для модели DeliveryAttempt."""

    def test_create_delivery_attempt(self):
        """Тест создания попытки доставки."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
        )

        attempt = DeliveryAttempt.objects.create(
            notification=notification,
            channel=DeliveryAttempt.CHANNEL_EMAIL,
            status=DeliveryAttempt.STATUS_SUCCESS,
        )

        self.assertIsNotNone(attempt.id)
        self.assertEqual(attempt.notification, notification)
        self.assertEqual(attempt.channel, DeliveryAttempt.CHANNEL_EMAIL)
        self.assertEqual(attempt.status, DeliveryAttempt.STATUS_SUCCESS)

    def test_delivery_attempt_str(self):
        """Тест строкового представления."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
        )

        attempt = DeliveryAttempt.objects.create(
            notification=notification,
            channel=DeliveryAttempt.CHANNEL_EMAIL,
            status=DeliveryAttempt.STATUS_SUCCESS,
        )

        str_repr = str(attempt)
        self.assertIn(str(attempt.id), str_repr)
        self.assertIn(DeliveryAttempt.CHANNEL_EMAIL, str_repr)
        self.assertIn(DeliveryAttempt.STATUS_SUCCESS, str_repr)

    def test_delivery_attempt_with_error(self):
        """Тест попытки с ошибкой."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
        )

        attempt = DeliveryAttempt.objects.create(
            notification=notification,
            channel=DeliveryAttempt.CHANNEL_EMAIL,
            status=DeliveryAttempt.STATUS_FAILED,
            error_message="Connection timeout",
        )

        self.assertEqual(attempt.status, DeliveryAttempt.STATUS_FAILED)
        self.assertEqual(attempt.error_message, "Connection timeout")

    def test_delivery_attempt_relationship(self):
        """Тест связи с уведомлением."""
        notification = Notification.objects.create(
            to_email="test@example.com",
            body="Test message",
        )

        attempt1 = DeliveryAttempt.objects.create(
            notification=notification,
            channel=DeliveryAttempt.CHANNEL_EMAIL,
            status=DeliveryAttempt.STATUS_FAILED,
        )

        attempt2 = DeliveryAttempt.objects.create(
            notification=notification,
            channel=DeliveryAttempt.CHANNEL_SMS,
            status=DeliveryAttempt.STATUS_SUCCESS,
        )

        # Проверяем обратную связь
        attempts = notification.attempts.all()
        self.assertEqual(attempts.count(), 2)
        self.assertIn(attempt1, attempts)
        self.assertIn(attempt2, attempts)

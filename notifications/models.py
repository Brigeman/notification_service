import uuid

from django.db import models


class Notification(models.Model):
    """Модель уведомления."""

    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_DELIVERED = "delivered"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_FAILED, "Failed"),
    ]

    id: models.UUIDField = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # type: ignore[assignment]
    request_id: models.CharField | None = models.CharField(  # type: ignore[assignment]
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Идентификатор запроса для идемпотентности",
    )
    to_email: models.EmailField | None = models.EmailField(null=True, blank=True)  # type: ignore[assignment]
    to_phone: models.CharField | None = models.CharField(max_length=20, null=True, blank=True)  # type: ignore[assignment]
    to_telegram_chat_id: models.CharField | None = models.CharField(max_length=100, null=True, blank=True)  # type: ignore[assignment]
    subject: models.CharField | None = models.CharField(max_length=255, null=True, blank=True)  # type: ignore[assignment]
    body: models.TextField = models.TextField()  # type: ignore[assignment]
    channels: models.JSONField = models.JSONField(  # type: ignore[assignment]
        default=list,
        help_text='Список каналов в порядке приоритета, например: ["email", "sms", "telegram"]',
    )
    status: models.CharField = models.CharField(  # type: ignore[assignment]
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    used_channel: models.CharField | None = models.CharField(  # type: ignore[assignment]
        max_length=20,
        null=True,
        blank=True,
        help_text="Канал, через который успешно доставлено уведомление",
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)  # type: ignore[assignment]
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)  # type: ignore[assignment]

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["request_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Notification {self.id} - {self.status}"


class DeliveryAttempt(models.Model):
    """Модель попытки доставки уведомления."""

    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    CHANNEL_EMAIL = "email"
    CHANNEL_SMS = "sms"
    CHANNEL_TELEGRAM = "telegram"

    CHANNEL_CHOICES = [
        (CHANNEL_EMAIL, "Email"),
        (CHANNEL_SMS, "SMS"),
        (CHANNEL_TELEGRAM, "Telegram"),
    ]

    id: models.UUIDField = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # type: ignore[assignment]
    notification: models.ForeignKey = models.ForeignKey(  # type: ignore[assignment]
        Notification,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    channel: models.CharField = models.CharField(max_length=20, choices=CHANNEL_CHOICES)  # type: ignore[assignment]
    status: models.CharField = models.CharField(max_length=20, choices=STATUS_CHOICES)  # type: ignore[assignment]
    error_message: models.TextField | None = models.TextField(null=True, blank=True)  # type: ignore[assignment]
    attempted_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)  # type: ignore[assignment]

    class Meta:
        ordering = ["attempted_at"]
        indexes = [
            models.Index(fields=["notification", "attempted_at"]),
            models.Index(fields=["channel", "status"]),
        ]

    def __str__(self) -> str:
        return f"Attempt {self.id} - {self.channel} - {self.status}"

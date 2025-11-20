from django.contrib import admin

from notifications.models import DeliveryAttempt, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Админка для уведомлений."""

    list_display = ["id", "status", "used_channel", "to_email", "to_phone", "created_at"]
    list_filter = ["status", "used_channel", "created_at"]
    search_fields = ["id", "request_id", "to_email", "to_phone", "to_telegram_chat_id"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        (
            "Основная информация",
            {
                "fields": ("id", "request_id", "status", "used_channel"),
            },
        ),
        (
            "Получатель",
            {
                "fields": ("to_email", "to_phone", "to_telegram_chat_id"),
            },
        ),
        (
            "Содержание",
            {
                "fields": ("subject", "body", "channels"),
            },
        ),
        (
            "Временные метки",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


@admin.register(DeliveryAttempt)
class DeliveryAttemptAdmin(admin.ModelAdmin):
    """Админка для попыток доставки."""

    list_display = ["id", "notification", "channel", "status", "attempted_at"]
    list_filter = ["channel", "status", "attempted_at"]
    search_fields = ["notification__id", "channel", "error_message"]
    readonly_fields = ["id", "attempted_at"]
    fieldsets = (
        (
            "Основная информация",
            {
                "fields": ("id", "notification", "channel", "status"),
            },
        ),
        (
            "Детали",
            {
                "fields": ("error_message", "attempted_at"),
            },
        ),
    )

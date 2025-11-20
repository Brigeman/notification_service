from rest_framework import serializers

from notifications.models import DeliveryAttempt, Notification


class DeliveryAttemptSerializer(serializers.ModelSerializer):
    """Сериализатор для попытки доставки."""

    class Meta:
        model = DeliveryAttempt
        fields = ["channel", "status", "error_message", "attempted_at"]


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания уведомления."""

    request_id = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=True,
        help_text="Идентификатор запроса для идемпотентности",
    )
    channels = serializers.ListField(
        child=serializers.ChoiceField(choices=["email", "sms", "telegram"]),
        required=False,
        allow_empty=False,
        help_text="Список каналов в порядке приоритета",
    )

    class Meta:
        model = Notification
        fields = [
            "request_id",
            "to_email",
            "to_phone",
            "to_telegram_chat_id",
            "subject",
            "body",
            "channels",
        ]

    def validate(self, attrs):
        """Проверяет, что указан хотя бы один контакт."""
        to_email = attrs.get("to_email")
        to_phone = attrs.get("to_phone")
        to_telegram_chat_id = attrs.get("to_telegram_chat_id")

        if not any([to_email, to_phone, to_telegram_chat_id]):
            raise serializers.ValidationError(
                "At least one contact method must be provided "
                "(to_email, to_phone, or to_telegram_chat_id)",
            )

        return attrs

    def validate_channels(self, value):
        """Проверяет валидность каналов."""
        valid_channels = {"email", "sms", "telegram"}
        if not all(channel in valid_channels for channel in value):
            raise serializers.ValidationError(
                f"Invalid channels. Allowed: {valid_channels}",
            )
        return value


class NotificationResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа при создании уведомления."""

    used_channel = serializers.CharField(read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "status", "used_channel"]


class NotificationDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра уведомления."""

    attempts = DeliveryAttemptSerializer(many=True, read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "status",
            "subject",
            "body",
            "to_email",
            "to_phone",
            "to_telegram_chat_id",
            "channels",
            "used_channel",
            "created_at",
            "updated_at",
            "attempts",
        ]

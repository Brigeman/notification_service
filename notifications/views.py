import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from notifications.models import Notification
from notifications.serializers import (
    NotificationCreateSerializer,
    NotificationDetailSerializer,
    NotificationResponseSerializer,
)
from notifications.tasks import send_notification_task

logger = logging.getLogger(__name__)


@api_view(["POST"])
def create_notification(request):
    """
    Создает и отправляет уведомление.

    POST /api/notifications/
    """
    serializer = NotificationCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Проверка идемпотентности
    request_id = serializer.validated_data.get("request_id")
    if request_id:
        existing_notification = Notification.objects.filter(request_id=request_id).first()
        if existing_notification:
            logger.info(
                f"Idempotency check: notification with request_id={request_id} "
                f"already exists: {existing_notification.id}",
            )
            response_serializer = NotificationResponseSerializer(existing_notification)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

    # Создаем уведомление
    notification = serializer.save(status=Notification.STATUS_PENDING)

    # Запускаем асинхронную задачу отправки
    send_notification_task.delay(str(notification.id))
    logger.info(f"Created notification {notification.id}, task queued")

    # Возвращаем ответ с pending статусом
    response_serializer = NotificationResponseSerializer(notification)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def get_notification(request, notification_id):
    """
    Получает статус уведомления и историю попыток доставки.

    GET /api/notifications/{id}/
    """
    notification = get_object_or_404(Notification, id=notification_id)
    serializer = NotificationDetailSerializer(notification)
    return Response(serializer.data)

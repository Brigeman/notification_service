from django.urls import path

from notifications import views

app_name = "notifications"

urlpatterns = [
    path("notifications/", views.create_notification, name="create"),
    path("notifications/<uuid:notification_id>/", views.get_notification, name="detail"),
]

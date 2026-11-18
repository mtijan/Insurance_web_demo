from django.urls import path, re_path

from apps.notifications.views import (
    NotificationListView,
    NotificationReadAllView,
    NotificationReadView,
)

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("read-all/", NotificationReadAllView.as_view(), name="notification-read-all"),
    re_path(r"^(?P<pk>[^/]+)/read/$", NotificationReadView.as_view(), name="notification-read"),
]

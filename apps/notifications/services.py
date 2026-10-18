"""Small helpers so other apps never build Notification rows by hand."""
from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


def notify_user(user, title, body="", kind=Notification.Kind.SYSTEM, url=""):
    if user is None:
        return None
    return Notification.objects.create(user=user, title=title, body=body, kind=kind, url=url)


def notify_role(role, title, body="", kind=Notification.Kind.SYSTEM, url=""):
    created = []
    for user in User.objects.filter(role=role, is_active=True):
        created.append(notify_user(user, title, body, kind, url))
    return created


def notify_user_ref(user_id, title, body="", kind=Notification.Kind.SYSTEM, url=""):
    user = User.objects.filter(pk=user_id).first()
    return notify_user(user, title, body, kind, url)

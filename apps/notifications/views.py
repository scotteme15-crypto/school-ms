"""The signed-in user's notification inbox.

Every query is scoped to ``request.user``; foreign notifications resolve to a
404 so one user can never read or mutate another's inbox.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Notification


def _redirect_back(request):
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(target)
    return redirect("notifications:list")


@login_required
def list_view(request):
    notifications = Notification.objects.filter(user=request.user)
    context = {
        "page_title": "Notifications",
        "page_obj": Paginator(notifications, 20).get_page(request.GET.get("page")),
        "unread_count": notifications.filter(read=False).count(),
    }
    return render(request, "notifications/list.html", context)


@login_required
@require_POST
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if not notification.read:
        notification.read = True
        notification.save(update_fields=["read"])
    return _redirect_back(request)


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    messages.success(request, "All notifications marked as read.")
    return _redirect_back(request)


@login_required
@require_POST
def delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    messages.success(request, "Notification removed.")
    return _redirect_back(request)

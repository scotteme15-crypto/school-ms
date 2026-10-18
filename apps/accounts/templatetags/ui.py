"""Template helpers that mirror the original single-file UI kit."""
from decimal import Decimal, InvalidOperation

from django import template
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from apps.accounts.icons import ICON

register = template.Library()

STATUS_CLASSES = {
    "approved": ("ok", "Approved"),
    "pending": ("warn", "Pending"),
    "rejected": ("bad", "Rejected"),
    "returned": ("info", "Returned"),
    "draft": ("", "Draft"),
}

PERSON_CLASSES = {
    "Active": "ok",
    "Inactive": "",
    "Graduated": "info",
    "Suspended": "bad",
    "On leave": "warn",
}


@register.simple_tag
def icon(name, size=17, cls=""):
    path = ICON.get(name, "")
    return format_html(
        '<svg class="ic {}" width="{}" height="{}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>',
        cls,
        size,
        size,
        mark_safe(path),
    )


@register.simple_tag
def status_badge(value):
    css, label = STATUS_CLASSES.get(value, ("", value))
    return format_html('<span class="badge {}"><span class="d"></span>{}</span>', css, label)


@register.simple_tag
def person_badge(value):
    return format_html('<span class="badge {}">{}</span>', PERSON_CLASSES.get(value, ""), value)


@register.simple_tag
def avatar(name, cls=""):
    return format_html('<span class="avatar {}" aria-hidden="true">{}</span>', cls, initials(name))


@register.filter
def initials(value):
    parts = str(value or "").split()
    return "".join(p[0] for p in parts[:2]).upper()


@register.filter
def dict_get(mapping, key):
    if hasattr(mapping, "get"):
        return mapping.get(key)
    return None


@register.filter
def pct(value):
    if value is None or value == "":
        return "—"
    try:
        return f"{Decimal(str(value)):.1f}%"
    except (InvalidOperation, ValueError):
        return value


@register.filter
def num(value):
    if value is None or value == "":
        return "—"
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return value
    return f"{d:f}".rstrip("0").rstrip(".") if "." in f"{d:f}" else f"{d:f}"


@register.simple_tag(takes_context=True)
def active_if(context, url_name, css="on"):
    """Add a class when the current request path matches a named URL."""
    request = context.get("request")
    if request is None:
        return ""
    try:
        return css if request.path == reverse(url_name) else ""
    except Exception:
        return ""


@register.simple_tag
def querystring(request, **kwargs):
    """Rebuild the current query string with the given overrides."""
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value in (None, ""):
            params.pop(key, None)
        else:
            params[key] = value
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else ""

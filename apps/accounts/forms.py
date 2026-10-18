"""Forms for authentication and profile management."""
from django import forms
from django.contrib.auth.forms import (
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)

from .models import User


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "e.g. admin", "autocomplete": "username", "autofocus": True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "••••••••", "autocomplete": "current-password", "style": "padding-right:42px"}
        )
    )
    remember = forms.BooleanField(required=False)

    error_messages = {
        "invalid_login": "That username and password did not match an active account.",
    }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["full_name", "email", "phone"]
        labels = {"full_name": "Full name", "email": "Email address", "phone": "Phone"}


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"autocomplete": "new-password"})


class StyledPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"})
    )


class StyledSetPasswordForm(SetPasswordForm):
    pass


class UserAdminForm(forms.ModelForm):
    """Used by the registrar to create or edit a login account."""

    class Meta:
        model = User
        fields = ["username", "full_name", "email", "phone", "role", "title", "is_active"]

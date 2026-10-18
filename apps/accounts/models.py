"""Custom user model with a role field driving all authorisation."""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Manager that always creates users through ``set_password``."""

    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError("The username must be set")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.STUDENT)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("full_name", username)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if not extra_fields.get("full_name"):
            extra_fields["full_name"] = username
        return self._create_user(username, password, **extra_fields)


class User(AbstractUser):
    """A single account table for administrators, teachers and students."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        TEACHER = "teacher", "Teacher"
        STUDENT = "student", "Student"

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.STUDENT, db_index=True)
    full_name = models.CharField(max_length=150, blank=True)
    title = models.CharField(max_length=120, blank=True, help_text="Displayed under the name, e.g. 'Registrar'.")
    phone = models.CharField(max_length=32, blank=True)
    must_change_password = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    class Meta:
        ordering = ["full_name", "username"]

    def __str__(self):
        return self.full_name or self.username

    # ------------------------------------------------------------------ role
    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_teacher_role(self) -> bool:
        return self.role == self.Role.TEACHER

    @property
    def is_student_role(self) -> bool:
        return self.role == self.Role.STUDENT

    # --------------------------------------------------------------- display
    @property
    def display_name(self) -> str:
        return self.full_name or self.username

    @property
    def initials(self) -> str:
        parts = (self.full_name or self.username).split()
        return "".join(p[0] for p in parts[:2]).upper()

    @property
    def role_label(self) -> str:
        return self.get_role_display()

    # ------------------------------------------------------------- profiles
    @property
    def teacher_profile(self):
        return getattr(self, "teacher_profile", None)

    @property
    def student_profile(self):
        return getattr(self, "student_profile", None)

    def touch_last_seen(self):
        from django.utils import timezone

        self.last_seen = timezone.now()
        self.save(update_fields=["last_seen"])

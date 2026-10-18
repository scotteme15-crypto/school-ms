"""Authentication: login, logout, throttling and route protection."""
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .factories import build_school


class LoginTests(TestCase):
    def setUp(self):
        cache.clear()
        self.fx = build_school()

    def test_login_page_renders(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)

    def test_successful_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "admin", "password": "admin123"}
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_wrong_password_does_not_log_in(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "admin", "password": "nope"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(LOGIN_MAX_ATTEMPTS=3)
    def test_repeated_failures_lock_the_account_out(self):
        url = reverse("accounts:login")
        for _ in range(3):
            self.client.post(url, {"username": "admin", "password": "wrong"})
        response = self.client.post(url, {"username": "admin", "password": "wrong"})
        self.assertContains(response, "Too many failed attempts")

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_logout_is_post_only(self):
        self.client.force_login(self.fx.admin)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)


class DashboardDispatchTests(TestCase):
    def setUp(self):
        self.fx = build_school()

    def test_admin_sees_admin_dashboard(self):
        self.client.force_login(self.fx.admin)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/admin_dashboard.html")

    def test_teacher_sees_teacher_dashboard(self):
        self.client.force_login(self.fx.teacher_user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/teacher_dashboard.html")

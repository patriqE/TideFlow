import os
from pathlib import Path
import runpy
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase


SETTINGS_PATH = Path(__file__).resolve().parent.parent / "tideflow_backend" / "settings.py"


class EnvironmentSettingsTests(SimpleTestCase):
    def load_settings(self, **overrides):
        environment = {"DJANGO_SECRET_KEY": "test-only-settings-key", **overrides}
        with patch.dict(os.environ, environment, clear=True):
            return runpy.run_path(str(SETTINGS_PATH))

    def test_missing_secret_fails_startup(self):
        for value in ("", "   "):
            with self.subTest(value=value):
                with self.assertRaisesMessage(ImproperlyConfigured, "DJANGO_SECRET_KEY"):
                    self.load_settings(DJANGO_SECRET_KEY=value)

    def test_safe_defaults(self):
        settings = self.load_settings()
        self.assertFalse(settings["DEBUG"])
        self.assertNotIn("*", settings["ALLOWED_HOSTS"])
        self.assertEqual(settings["REDIS_URL"], "redis://127.0.0.1:6379/0")
        self.assertEqual(settings["PAYSTACK_SECRET_KEY"], "")

    def test_environment_overrides(self):
        settings = self.load_settings(
            DJANGO_DEBUG="true", DJANGO_ALLOWED_HOSTS=" api.example.com, ,localhost ",
            REDIS_URL="redis://custom:6379/2",
        )
        self.assertTrue(settings["DEBUG"])
        self.assertEqual(settings["ALLOWED_HOSTS"], ["api.example.com", "localhost"])
        self.assertEqual(settings["REDIS_URL"], "redis://custom:6379/2")

    def test_false_string_does_not_enable_debug(self):
        self.assertFalse(self.load_settings(DJANGO_DEBUG="false")["DEBUG"])

    def test_webhook_secret_defaults_to_payment_secret(self):
        settings = self.load_settings(PAYSTACK_SECRET_KEY="test-only-payment-key")
        self.assertEqual(settings["PAYSTACK_WEBHOOK_SECRET"], "test-only-payment-key")
        settings = self.load_settings(
            PAYSTACK_SECRET_KEY="test-only-payment-key", PAYSTACK_WEBHOOK_SECRET="test-only-webhook-key",
        )
        self.assertEqual(settings["PAYSTACK_WEBHOOK_SECRET"], "test-only-webhook-key")

import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from .auth import create_access_token
from .models import Profile


class AccountValidationTests(TestCase):
    def register(self, **overrides):
        return self.client.post("/accounts/register/", {
            "email": "person@example.com", "phone": "+2348012345678", "password": "Harbor!72-Sailing",
            **overrides,
        }, content_type="application/json")

    def test_registration_normalizes_email_and_hashes_password(self):
        self.assertEqual(self.register(email=" PERSON@Example.com ").status_code, 201)
        user = get_user_model().objects.get()
        self.assertEqual(user.email, "person@example.com")
        self.assertTrue(user.check_password("Harbor!72-Sailing"))
        self.assertEqual(user.profile.role, Profile.ROLE_PASSENGER)

    def test_duplicate_phone_creates_no_partial_user(self):
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.register(email="second@example.com").status_code, 400)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(Profile.objects.count(), 1)

    def test_duplicate_email_is_case_insensitive(self):
        self.register()
        self.assertEqual(self.register(email="PERSON@EXAMPLE.COM", phone="+2348012345679").status_code, 400)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_profile_insert_conflict_rolls_back_user(self):
        with patch("accounts.views.Profile.objects.create", side_effect=IntegrityError("Concurrent duplicate")):
            self.assertEqual(self.register().status_code, 400)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_invalid_identifiers_and_passwords_are_rejected(self):
        cases = [{"email": "invalid"}, {"email": "x" * 151 + "@example.com"}, {"phone": "12"},
                 {"phone": "letters"}, {"password": "short"}, {"password": "123456789"},
                 {"password": "password"}, {"email": []}, {"phone": 123}, {"password": False}]
        for values in cases:
            with self.subTest(values=values):
                self.assertEqual(self.register(**values).status_code, 400)
                self.assertEqual(get_user_model().objects.count(), 0)

    def test_non_object_payloads_are_rejected_by_account_endpoints(self):
        for endpoint in ("register", "login", "refresh", "logout"):
            for data in ([], None, "text", 2):
                with self.subTest(endpoint=endpoint, data=data):
                    response = self.client.post(f"/accounts/{endpoint}/", json.dumps(data), content_type="application/json")
                    self.assertEqual(response.status_code, 400)

    def test_phone_only_registration_and_login(self):
        self.assertEqual(self.register(email="").status_code, 201)
        response = self.client.post("/accounts/login/", {"phone": "+2348012345678", "password": "Harbor!72-Sailing"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)

    def test_legacy_case_duplicate_email_fails_login_without_server_error(self):
        User = get_user_model()
        User.objects.create_user(username="old-1", email="Person@example.com", password="Harbor!72-Sailing")
        User.objects.create_user(username="old-2", email="person@example.com", password="Harbor!72-Sailing")
        response = self.client.post("/accounts/login/", {"email": "person@example.com", "password": "Harbor!72-Sailing"}, content_type="application/json")
        self.assertEqual(response.status_code, 401)

    def test_invalid_roles_and_ids_do_not_change_privileges(self):
        admin = get_user_model().objects.create_user(username="admin", is_superuser=True)
        user = get_user_model().objects.create_user(username="target")
        Profile.objects.create(user=user)
        headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(admin)}"}
        for data in ({"user_id": user.pk, "role": "OWNER"}, {"user_id": True, "role": "ADMIN"},
                     {"user_id": [], "role": "ADMIN"}, {"user_id": user.pk, "role": []}):
            self.assertEqual(self.client.post("/accounts/set-role/", data, content_type="application/json", **headers).status_code, 400)
        user.refresh_from_db()
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.profile.role, Profile.ROLE_PASSENGER)

    def test_role_and_flags_roll_back_together(self):
        admin = get_user_model().objects.create_user(username="admin", is_superuser=True)
        target = get_user_model().objects.create_user(username="target")
        Profile.objects.create(user=target)
        with patch("django.contrib.auth.models.User.save", side_effect=RuntimeError("Save failed")):
            with self.assertRaises(RuntimeError):
                self.client.post("/accounts/set-role/", {"user_id": target.pk, "role": "ADMIN"}, content_type="application/json",
                                 HTTP_AUTHORIZATION=f"Bearer {create_access_token(admin)}")
        self.assertEqual(Profile.objects.get(user=target).role, Profile.ROLE_PASSENGER)

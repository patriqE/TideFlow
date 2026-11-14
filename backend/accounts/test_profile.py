import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from .auth import create_access_token, create_refresh_token
from .models import Profile


class ProfileApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="person@example.com", email="person@example.com", password="Harbor!72-Sailing",
        )
        self.profile = Profile.objects.create(user=self.user, phone="+2348012345678", full_name="Ada Okafor")
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(self.user)}"}

    def edit(self, data):
        return self.client.patch("/accounts/profile/", json.dumps(data), content_type="application/json", **self.headers)

    def test_get_returns_only_current_users_profile_fields(self):
        response = self.client.get("/accounts/profile/", **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id": self.user.pk, "full_name": "Ada Okafor", "email": self.user.email,
                                           "phone": self.profile.phone, "role": "PASSENGER"})

    def test_registration_saves_full_name_and_keeps_name_optional(self):
        for index, extra in enumerate(({"full_name": "  José Ada Okafor  "}, {})):
            response = self.client.post("/accounts/register/", {
                "email": f"new{index}@example.com", "password": "Harbor!72-Sailing", **extra,
            }, content_type="application/json")
            self.assertEqual(response.status_code, 201)
            profile = Profile.objects.get(user_id=response.json()["id"])
            self.assertEqual(profile.full_name, "José Ada Okafor" if index == 0 else "")

    def test_anonymous_cookie_only_and_refresh_tokens_cannot_access_profile(self):
        for method in (self.client.get, self.client.patch):
            self.assertEqual(method("/accounts/profile/").status_code, 401)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/accounts/profile/").status_code, 401)
        refresh, _, _ = create_refresh_token(self.user)
        self.assertEqual(self.client.get("/accounts/profile/", HTTP_AUTHORIZATION=f"Bearer {refresh}").status_code, 401)

    def test_inactive_account_cannot_access_or_edit(self):
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=False)
        self.assertEqual(self.client.get("/accounts/profile/", **self.headers).status_code, 401)
        self.assertEqual(self.edit({"full_name": "Changed"}).status_code, 401)

    def test_partial_name_update_preserves_contacts(self):
        response = self.edit({"full_name": "  Ada N. Okafor "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["full_name"], "Ada N. Okafor")
        self.assertEqual(response.json()["email"], self.user.email)
        self.assertEqual(response.json()["phone"], self.profile.phone)

    def test_contact_update_changes_login_and_removes_old_identifiers(self):
        response = self.edit({"email": " NEW@Example.com ", "phone": "+2348012345679"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "new@example.com")
        for data, expected in (({"email": "NEW@example.com"}, 200), ({"phone": "+2348012345679"}, 200),
                               ({"email": self.user.email}, 401), ({"phone": self.profile.phone}, 401)):
            response = self.client.post("/accounts/login/", {**data, "password": "Harbor!72-Sailing"}, content_type="application/json")
            self.assertEqual(response.status_code, expected)

    def test_duplicate_contacts_do_not_partially_change_name(self):
        other = get_user_model().objects.create_user(username="other@example.com", email="other@example.com")
        Profile.objects.create(user=other, phone="+2348012345679")
        for data in ({"email": "OTHER@example.com"}, {"phone": "+2348012345679"}):
            self.assertEqual(self.edit({"full_name": "Changed", **data}).status_code, 400)
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.full_name, "Ada Okafor")

    def test_profile_conflict_rolls_back_user_contact_change(self):
        with patch("accounts.views.Profile.save", side_effect=IntegrityError("Duplicate phone race")):
            self.assertEqual(self.edit({"email": "new@example.com"}).status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "person@example.com")
        self.assertEqual(self.user.username, "person@example.com")

    def test_last_login_identifier_cannot_be_removed(self):
        self.assertEqual(self.edit({"email": "", "phone": ""}).status_code, 400)
        self.assertEqual(self.edit({"email": ""}).status_code, 200)
        self.assertEqual(self.edit({"phone": ""}).status_code, 400)
        self.assertEqual(self.edit({"email": "new@example.com", "phone": ""}).status_code, 200)

    def test_privilege_and_cross_user_updates_are_rejected(self):
        for field in ("role", "is_staff", "is_superuser", "user_id", "id", "username", "password"):
            self.assertEqual(self.edit({field: "ADMIN"}).status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_superuser)
        self.assertEqual(Profile.objects.get(user=self.user).role, Profile.ROLE_PASSENGER)

    def test_invalid_payloads_and_names_are_rejected(self):
        for data in ([], None, "text", {}, {"full_name": None}, {"full_name": "x" * 256},
                     {"full_name": "Ada\nOkafor"}, {"email": "bad"}, {"phone": "123"}):
            with self.subTest(data=data):
                self.assertEqual(self.edit(data).status_code, 400)
        for name in (None, "x" * 256):
            response = self.client.post("/accounts/register/", {"email": "new@example.com", "password": "Harbor!72-Sailing", "full_name": name}, content_type="application/json")
            self.assertEqual(response.status_code, 400)

    def test_existing_account_without_profile_has_safe_fallback(self):
        self.profile.delete()
        get_user_model().objects.filter(pk=self.user.pk).update(first_name="Ada", last_name="Okafor", is_superuser=True)
        response = self.client.get("/accounts/profile/", **self.headers)
        self.assertEqual(response.json()["full_name"], "Ada Okafor")
        self.assertEqual(response.json()["role"], "ADMIN")
        self.assertFalse(Profile.objects.filter(user=self.user).exists())
        response = self.edit({"full_name": "Ada Updated"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Profile.objects.get(user=self.user).role, "ADMIN")

    def test_unsupported_method_cannot_delete_profile(self):
        self.assertEqual(self.client.delete("/accounts/profile/", **self.headers).status_code, 405)
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

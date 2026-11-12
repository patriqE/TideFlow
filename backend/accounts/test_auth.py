from datetime import timedelta

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .auth import create_access_token, create_refresh_token
from .models import Profile, Session


class TokenAuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="passenger@example.com", email="passenger@example.com",
            password="test-password-123",
        )
        Profile.objects.create(user=cls.user)

    def protected_request(self, token):
        return self.client.get("/fleet/bookings/", HTTP_AUTHORIZATION=f"Bearer {token}")

    def make_refresh_session(self):
        token, jti, expires_at = create_refresh_token(self.user)
        session = Session.objects.create(user=self.user, jti=jti, expires_at=expires_at)
        return token, session

    def refresh(self, token):
        return self.client.post("/accounts/refresh/", {"refresh": token}, content_type="application/json")

    def test_active_user_access_token_is_accepted(self):
        self.assertEqual(self.protected_request(create_access_token(self.user)).status_code, 200)

    def test_refresh_token_cannot_authenticate_before_or_after_logout(self):
        token, session = self.make_refresh_session()
        self.assertEqual(self.protected_request(token).status_code, 401)
        response = self.client.post("/accounts/logout/", {"refresh": token}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        session.refresh_from_db()
        self.assertTrue(session.revoked)
        self.assertEqual(self.protected_request(token).status_code, 401)
        self.assertEqual(self.refresh(token).status_code, 401)

    def test_refresh_rotation_still_works_and_old_token_cannot_be_reused(self):
        token, session = self.make_refresh_session()
        response = self.refresh(token)
        self.assertEqual(response.status_code, 200)
        tokens = response.json()
        self.assertEqual(self.protected_request(tokens["access"]).status_code, 200)
        self.assertEqual(self.protected_request(tokens["refresh"]).status_code, 401)
        self.assertEqual(self.refresh(token).status_code, 401)
        self.assertEqual(self.refresh(tokens["refresh"]).status_code, 200)
        session.refresh_from_db()
        self.assertTrue(session.revoked)

    def test_access_token_cannot_be_used_for_refresh(self):
        self.assertEqual(self.refresh(create_access_token(self.user)).status_code, 401)
        self.assertEqual(Session.objects.count(), 0)

    def test_deactivated_user_cannot_authenticate_login_or_refresh(self):
        access = create_access_token(self.user)
        refresh, session = self.make_refresh_session()
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=False)
        self.assertEqual(self.protected_request(access).status_code, 401)
        self.assertEqual(self.refresh(refresh).status_code, 401)
        response = self.client.post(
            "/accounts/login/", {"email": self.user.email, "password": "test-password-123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Session.objects.count(), 1)

    def test_active_user_can_login(self):
        response = self.client.post(
            "/accounts/login/", {"email": self.user.email, "password": "test-password-123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.protected_request(response.json()["access"]).status_code, 200)

    def test_expired_session_cannot_refresh_even_with_unexpired_token(self):
        token, session = self.make_refresh_session()
        Session.objects.filter(pk=session.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.refresh(token).status_code, 401)
        self.assertEqual(Session.objects.count(), 1)

    def test_refresh_session_must_belong_to_token_user(self):
        token, session = self.make_refresh_session()
        other = get_user_model().objects.create_user(username="other")
        Session.objects.filter(pk=session.pk).update(user=other)
        self.assertEqual(self.refresh(token).status_code, 401)

    def test_invalid_access_claims_are_rejected(self):
        now = timezone.now()
        claims = {"user_id": self.user.pk, "type": "access", "iat": now, "exp": now + timedelta(minutes=15)}
        invalid_claims = [
            {**claims, "exp": now - timedelta(seconds=1)},
            {**claims, "type": "unknown"},
            *[{**claims, "user_id": value} for value in (None, True, [], "invalid", 1.5)],
            *[{key: value for key, value in claims.items() if key != missing}
              for missing in ("exp", "iat", "user_id", "type")],
        ]
        for payload in invalid_claims:
            with self.subTest(payload=payload):
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
                self.assertEqual(self.protected_request(token).status_code, 401)

    def test_malformed_and_wrongly_signed_tokens_are_rejected(self):
        token = create_access_token(self.user)
        claims = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        wrong_signature = jwt.encode(claims, "different-test-signing-key-for-invalid-token", algorithm="HS256")
        for value in ("", "not-a-jwt", wrong_signature):
            with self.subTest(token=value):
                self.assertEqual(self.protected_request(value).status_code, 401)

    def test_deleted_user_token_is_rejected(self):
        token = create_access_token(self.user)
        self.user.delete()
        self.assertEqual(self.protected_request(token).status_code, 401)

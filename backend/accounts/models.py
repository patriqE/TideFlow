from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)

    def __str__(self):
        return self.phone or getattr(self.user, "email", "") or str(self.user)


class Session(models.Model):
    """Tracks refresh tokens / user sessions for simple session management."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    jti = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)

    def __str__(self):
        return f"Session(user={self.user_id}, jti={self.jti}, revoked={self.revoked})"

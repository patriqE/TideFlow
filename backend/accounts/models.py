from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)

    def __str__(self):
        return self.phone or getattr(self.user, "email", "") or str(self.user)

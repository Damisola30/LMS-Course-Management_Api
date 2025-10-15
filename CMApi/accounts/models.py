from django.contrib.auth.models import AbstractUser
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import models, IntegrityError

def default_expires_at():
    return timezone.now() + timedelta(days=1)

# Create your models here.


# Create your models here.
class User(AbstractUser):
    # the different types of roles/users  avaliable
    ROLE_CHOICES = (
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('guest', 'Guest'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest')

    def __str__(self):
        return f"{self.username} ({self.role})"


# class Workspace(models.Model):
#     name = models.CharField(max_length=150, unique=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.name


class ApiKey(models.Model):
    developer = models.OneToOneField(User, on_delete=models.CASCADE, related_name="api_key")
    key        = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField(default=default_expires_at)  # ✅ no lambda
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.workspace.name} - {self.key[:8]}..."

    @classmethod
    def generate_key(cls, length=24):
        # cryptographically secure, URL-safe
        import secrets
        return secrets.token_urlsafe(length)

    @classmethod
    def create_for_workspace(cls, workspace, ttl_hours=24):
        # still let callers override TTL
        expires = timezone.now() + timedelta(hours=ttl_hours) if ttl_hours else None
        # optionally retry on a rare uniqueness collision
        for _ in range(5):
            try:
                return cls.objects.create(
                    workspace=workspace,
                    key=cls.generate_key(),
                    expires_at=expires if ttl_hours is not None else default_expires_at(),
                )
            except IntegrityError:
                continue
        raise RuntimeError("Could not generate a unique API key after several attempts.")

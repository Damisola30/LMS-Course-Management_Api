from django.contrib.auth.models import AbstractUser
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import models, IntegrityError
import secrets

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
    developer  = models.OneToOneField(User, on_delete=models.CASCADE, related_name="api_key")
    HashedKey   = models.CharField(max_length=128, unique=True, db_index=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.developer.username}- {self.HashedKey[:8]}..."

    @classmethod
    def generate_key(cls, length=24):
        return secrets.token_urlsafe(length)

    @classmethod
    def create_for_dev(cls, developer):
        # still let callers override TTL
        #expires = timezone.now() + timedelta(hours=ttl_hours) if ttl_hours else None
        # optionally retry on a rare uniqueness collision
        for _ in range(5):
            try:
                raw_key = cls.generate_key()
                key_hash = cls.hash_key(raw_key)
                obj = cls.objects.create(developer=developer, HashedKey=key_hash)
                return obj, raw_key  # Return both object and plaintext for showing once
            except IntegrityError:
                continue
        raise RuntimeError("Could not generate a unique API key after several attempts.")
    @staticmethod
    def hash_key(raw_key):
        import hashlib
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def verify_key(self, raw_key):
        """Compare a provided API key to its hash."""
        return self.key_hash == self.hash_key(raw_key)
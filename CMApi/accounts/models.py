from django.db import models
from django.contrib.auth.models import AbstractUser

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


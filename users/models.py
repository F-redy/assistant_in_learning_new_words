from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    LANGUAGES = (
        ("UA", "Ukrainian"),
        ("EN", "English"),
        ("RU", "Russian"),

    )
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=25, unique=True)
    native_language = models.CharField(max_length=2, choices=LANGUAGES, default="UA")
    language_to_learn = models.CharField(max_length=2, choices=LANGUAGES, default='EN')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

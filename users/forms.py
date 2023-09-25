from django.forms import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from users.models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        # Поля, которые будут отображены
        fields = ("username", "email", "phone", "native_language", "language_to_learn")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        # Поля, которые будут отображены
        fields = ("username", "email", "phone", "native_language", "language_to_learn")

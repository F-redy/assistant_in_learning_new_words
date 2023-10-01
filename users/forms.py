from django.contrib.auth.forms import (AuthenticationForm, UserChangeForm,
                                       UserCreationForm)
from django.forms import forms

from users.models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Класс-форма для регистрации пользователей, на основе базового класса регистрации от django"""

    class Meta:
        model = CustomUser
        # Поля, которые будут отображены
        fields = ("username", "email", "phone")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        # Поля, которые будут отображены
        fields = ("username", "email", "phone")


class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "password")

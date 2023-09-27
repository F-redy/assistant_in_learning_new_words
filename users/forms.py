from django.forms import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm

from users.models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Класс-форма для регистрации пользователей, на основе базового класса регистрации от django"""

    class Meta:
        model = CustomUser
        # Поля, которые будут отображены
        fields = ("username", "email", "phone", "native_language", "language_to_learn")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        # Поля, которые будут отображены
        fields = ("username", "email", "phone", "native_language", "language_to_learn")


class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "password")

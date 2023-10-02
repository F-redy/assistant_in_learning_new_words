from django.contrib.auth.forms import (AuthenticationForm, UserChangeForm,
                                       UserCreationForm)
from django import forms

from users.models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Класс-форма для регистрации пользователей, на основе базового класса регистрации от django"""
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'placeholder': 'Enter username'}))
    email = forms.CharField(label='Email', widget=forms.EmailInput(attrs={'placeholder': 'Enter email'}))
    phone = forms.CharField(label='Phone', widget=forms.TextInput(attrs={'placeholder': 'Enter phone'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}))
    password2 = forms.CharField(label='Password repeat',
                                widget=forms.PasswordInput(attrs={'placeholder': 'Enter password again'}))

    class Meta:
        model = CustomUser
        # Поля, которые будут отображены
        fields = ('username', 'email', 'phone', 'password1', 'password2')


class CustomUserChangeForm(UserChangeForm):
    username = forms.CharField(label='Changing Username',
                               widget=forms.TextInput(attrs={'placeholder': 'Enter username'}))
    email = forms.CharField(label='Changing Email', widget=forms.EmailInput(attrs={'placeholder': 'Enter email'}))
    phone = forms.CharField(label='Changing Phone', widget=forms.TextInput(attrs={'placeholder': 'Enter phone'}))

    class Meta:
        model = CustomUser
        # Поля, которые будут отображены
        fields = ("username", "email", "phone")


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'placeholder': 'Enter username'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}))

    class Meta:
        model = CustomUser
        fields = ("username", "password")

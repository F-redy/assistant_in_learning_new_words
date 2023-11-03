from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView  # Авторизация пользователя
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from users.forms import (CustomAuthenticationForm, CustomUserChangeForm,
                         CustomUserCreationForm)
from users.models import CustomUser


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("home")
    template_name = "users/signup.html"

    def get_context_data(self, **kwargs):
        context = super(SignUpView, self).get_context_data(**kwargs)
        context["title"] = "Sign UP"

        return context

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect("words:show_dictionaries")


class LogInView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = "users/login.html"
    success_url = reverse_lazy("words:show_dictionaries")

    def get_context_data(self, **kwargs):
        context = super(LogInView, self).get_context_data(**kwargs)
        context["title"] = "Log In"

        return context


class UserUpdateView(UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = "users/profile.html"

    def get_success_url(self):
        return reverse_lazy("users:profile", args=(self.object.id,))


def logout_and_redirect_to_login(request):
    logout(request)
    return redirect('users:login')

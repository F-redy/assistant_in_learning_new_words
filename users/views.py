from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView  # Авторизация пользователя

from users.forms import CustomUserCreationForm, CustomAuthenticationForm


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
        return redirect("home")


class LogInView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = "users/login.html"
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super(LogInView, self).get_context_data(**kwargs)
        context["title"] = "Log In"

        return context


def logout_and_redirect_to_login(request):
    logout(request)
    return redirect('users:login')

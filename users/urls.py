from django.urls import path
from django.contrib.auth.decorators import login_required

from .views import SignUpView, LogInView, UserUpdateView, logout_and_redirect_to_login

app_name = 'users'

urlpatterns = [
    path("signup/", SignUpView.as_view(), name='signup'),
    path("login/", LogInView.as_view(), name='login'),
    path("profile/<int:pk>", login_required(UserUpdateView.as_view()), name='profile'),
    path("logout/", logout_and_redirect_to_login, name='logout'),
]

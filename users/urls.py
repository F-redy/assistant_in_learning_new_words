from django.urls import path

from .views import SignUpView, LogInView, logout_and_redirect_to_login

app_name = 'users'

urlpatterns = [
    path("signup/", SignUpView.as_view(), name='signup'),
    path("login/", LogInView.as_view(), name='login'),
    path("logout/", logout_and_redirect_to_login, name='logout'),
]

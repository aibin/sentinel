from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from core import views

app_name = "core"
urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path(
        "forgot-password/", views.ForgotPasswordView.as_view(), name="forgot_password"
    ),
    path("reset-password/", views.ResetPasswordView.as_view(), name="reset_password"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout-success/", views.LogoutSuccessView.as_view(), name="logout-success"),
]

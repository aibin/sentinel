from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from core import views

app_name = "core"
urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path(
        "update-password/<token>/",
        views.PasswordSetupView.as_view(),
        name="update_password",
    ),
    path(
        "forgot-password/", views.ForgotPasswordView.as_view(), name="forgot_password"
    ),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout-success/", views.LogoutSuccessView.as_view(), name="logout-success"),
    path("success/", views.SuccessView.as_view(), name="success"),
]

# Create your views here.
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import View

from oidc_provider.models import Organization, OrganizationUser


# Create your views here.
class LoginView(View):
    def get(self, request):
        # Clear any existing messages
        messages.get_messages(request).used = True
        return render(request, "core/login.html", {"name": request.organization.name})

    def post(self, request):
        # Get the email and password from the POST data
        messages.get_messages(request).used = True
        email = request.POST.get("email")
        password = request.POST.get("password")
        next_url = request.GET.get("next", "")

        # Check if user is part of the organization
        user_exist = request.organization.get_all_users().filter(email=email).exists()
        if not user_exist:
            messages.error(
                request, "Invalid user. Please enter a valid email and password."
            )
            return render(
                request, "core/login.html", {"name": request.organization.name}
            )

        # Authenticate the user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # If the user is valid, log them in
            login(request, user)

            # Check if the "next" parameter is safe and redirect
            if next_url and url_has_allowed_host_and_scheme(
                next_url, settings.ALLOWED_HOSTS
            ):
                return redirect(next_url)
            else:
                # Redirect to OIDC authorize page or some default dashboard
                return redirect("oidc_provider:authorize")
        else:
            # Add an error message for invalid credentials
            messages.error(request, "Invalid email or password. Please try again.")
            return render(
                request, "core/login.html", {"name": request.organization.name}
            )


class ForgotPasswordView(View):
    def get(self, request):
        return render(request, "core/forgot-password.html")


class ResetPasswordView(View):
    def get(self, request):
        return render(request, "core/reset-password.html")


class RegisterView(View):
    def get(self, request):
        return render(request, "core/register.html")


class LogoutSuccessView(View):
    def get(self, request):
        return render(request, "core/logout-success.html")

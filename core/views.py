# Create your views here.
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import View

from core.constants import *
from core.email.tasks import send_password_reset_email
from core.models import PasswordToken
from oidc_provider.models import Client, Connection

User = get_user_model()


# Create your views here.
class LoginView(View):

    def build_social_login_url(self, request, provider):
        url = reverse(
            "social:begin",
            kwargs={
                "org_slug": request.organization.slug,
                "backend": provider.type,
            },
        )
        query = {"next": request.GET.get("next", "")}
        query_string = urlencode(query, safe="/")

        return f"{url}?{query_string}"

    def build_social_login_icon(self, provider):
        if provider.type == "google-oauth2":
            return svg_google
        elif provider.type == "microsoft-graph":
            return svg_microsoft

    def render_login_page(self, request):
        connection = None
        client = None
        try:
            client_id = request.session.get("client_id")
            client = Client.objects.get(client_id=client_id)
            organization_id = request.session.get("organization_id")

            connection = Connection.objects.get(
                organization_id=organization_id, client_id=client_id
            )
        except Connection.DoesNotExist:
            connection = None

        providers = []
        if connection:
            for provider in connection.identity_providers.all():
                providers.append(
                    {
                        "text": f"Login with {provider.get_type_display()}",
                        "url": self.build_social_login_url(request, provider),
                        "icon": self.build_social_login_icon(provider),
                    }
                )
        return render(
            request,
            "core/login.html",
            {
                "name": request.organization.name,
                "providers": providers,
                "can_register": (
                    connection.allow_registration
                    if connection
                    else client.allow_registration
                ),
            },
        )

    def get(self, request):
        # Clear any existing messages
        messages.get_messages(request).used = True
        return self.render_login_page(request)

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
                request,
                "Invalid user. Please enter a valid email and password.",
                extra_tags="alert-danger",
            )
            return self.render_login_page(request)

        # Check if user is active
        org_user = request.organization.get_organization_user_by_email(email=email)
        if not org_user.active:
            messages.info(
                request,
                "User is not active. Please contact your administrator.",
                extra_tags="alert-info",
            )
            return self.render_login_page(request)

        # Check if user is verified
        if not org_user.user.email_verified:
            messages.info(
                request,
                "User email is not verified. Please follow the link in the welcome email to verify your email.",
                extra_tags="alert-info",
            )
            return self.render_login_page(request)

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
                url = reverse("oidc_provider:authorize")
                return redirect(f"{url}?organization_id={request.organization.id}")
        else:
            # Add an error message for invalid credentials
            messages.error(
                request,
                "Invalid email or password. Please try again.",
                extra_tags="alert-danger",
            )
            return self.render_login_page(request)


class ForgotPasswordView(View):
    def get(self, request):
        messages.get_messages(request).used = True
        return render(request, "core/forgot-password.html")

    def post(self, request):
        messages.get_messages(request).used = True
        email = request.POST.get("email")
        if User.objects.filter(email=email).exists():
            # Create a password reset token
            organization = request.organization
            next_url = None
            if organization and organization.post_password_update_url:
                next_url = organization.post_password_update_url
            token = PasswordToken.objects.create(
                user=User.objects.get(email=email), purpose="reset", next_url=next_url
            )
            url = reverse("core:update_password", args=[token.token])
            url = request.build_absolute_uri(url)
            # Send password reset email
            send_password_reset_email.delay(
                User.objects.get(email=email).full_name,
                email,
                url,
            )

        messages.info(
            request,
            "If an account exists, you'll receive password reset instructions by email.",
            extra_tags="alert-info",
        )
        return render(request, "core/forgot-password.html")


class PasswordSetupView(View):
    def get(self, request, token):
        try:
            password_token = PasswordToken.objects.get(token=token)
            if password_token.is_valid():
                return render(
                    request,
                    "core/change-password.html",
                    {"purpose": password_token.purpose.capitalize()},
                )
            else:
                return render(request, "core/invalid-token.html")
        except PasswordToken.DoesNotExist:
            return render(request, "core/invalid-token.html")

    def post(self, request, token):
        try:
            password_token = PasswordToken.objects.get(token=token)
            if password_token.is_valid():
                new_password = request.POST.get("new_password")
                confirm_password = request.POST.get("confirm_password")
                if new_password != confirm_password:
                    messages.error(
                        request, "Passwords do not match.", extra_tags="alert-danger"
                    )
                    return render(request, "core/change-password.html")

                password_token.user.set_password(new_password)
                if password_token.purpose == "setup":
                    password_token.user.email_verified = True
                password_token.user.save()
                next_url = password_token.next_url
                password_token.used = True
                password_token.save()
                messages.success(
                    request,
                    "Password updated successfully. Please login now.",
                    extra_tags="alert-success",
                )
                if next_url:
                    return redirect(next_url)
                else:
                    # Redirect to success page core:success with POST data
                    return render(
                        request,
                        "core/success.html",
                        {
                            "title": "Password updated successfully",
                            "subtitle": "Please login with your new password.",
                        },
                    )
            else:
                return render(request, "core/invalid-token.html")
        except PasswordToken.DoesNotExist:
            return render(request, "core/invalid-token.html")


class RegisterView(View):
    def get(self, request):
        return render(request, "core/register.html")


class LogoutSuccessView(View):
    def get(self, request):
        return render(request, "core/logout-success.html")


class SuccessView(View):
    def post(self, request):
        title = request.POST.get("title")
        subtitle = request.POST.get("subtitle")
        return render(
            request, "core/success.html", {"title": title, "subtitle": subtitle}
        )

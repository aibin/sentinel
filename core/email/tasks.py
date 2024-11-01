from celery import shared_task
from django.conf import settings

from core.email.adapter import EmailAdapter


@shared_task
def send_setup_account_email(name, org_name, email, url):
    subject = f"Welcome to {org_name.capitalize()}!"
    template_name = "core/emails/setup-account.html"
    recipient_list = [email]
    context = {
        "name": name,
        "platform": settings.EMAIL_DEFAULT_PLATFORM.capitalize(),
        "url": url,
        "org_name": org_name.capitalize(),
    }

    EmailAdapter.send_email(subject, template_name, recipient_list, context)


@shared_task
def send_welcome_email(name, org_name, email, url):
    subject = f"Welcome to {org_name.capitalize()}!"
    template_name = "core/emails/welcome.html"
    recipient_list = [email]
    context = {
        "name": name,
        "platform": settings.EMAIL_DEFAULT_PLATFORM.capitalize(),
        "url": url,
        "org_name": org_name.capitalize(),
    }

    EmailAdapter.send_email(subject, template_name, recipient_list, context)


@shared_task
def send_password_reset_email(name, email, url):
    subject = "Password Reset"
    template_name = "core/emails/reset-password.html"
    recipient_list = [email]
    context = {
        "name": name,
        "platform": settings.EMAIL_DEFAULT_PLATFORM.capitalize(),
        "url": url,
    }

    EmailAdapter.send_email(subject, template_name, recipient_list, context)

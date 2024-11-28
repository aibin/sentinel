from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class EmailAdapter:
    @staticmethod
    def send_email(
        subject, template_name, recipient_list, context=None, from_email=None
    ):
        """
        Sends an email using the specified template.

        :param subject: Subject of the email
        :param template_name: Path to the email template
        :param recipient_list: List of email addresses to send to
        :param context: Context dictionary for rendering the template
        :param from_email: The sender's email address (defaults to DEFAULT_FROM_EMAIL)
        """
        if context is None:
            context = {}

        # Render email content
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)  # Fallback plain text version
        from_email = from_email or settings.DEFAULT_FROM_EMAIL

        if settings.ENV != "prod":
            recipient_list = [settings.DEFAULT_TO_EMAIL]

        # Send the email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
        )

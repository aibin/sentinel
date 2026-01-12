from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core import mail

from core.email.adapter import EmailAdapter
from core.email.tasks import (
    send_password_reset_email,
    send_setup_account_email,
    send_welcome_email,
)


class EmailAdapterTestCase(TestCase):
    """Test cases for EmailAdapter"""

    @override_settings(
        DEFAULT_FROM_EMAIL="noreply@test.com",
        ENV="local",
        DEFAULT_TO_EMAIL="test@crewii.com",
        EMAIL_DEFAULT_PLATFORM="sentinel",
    )
    @patch("core.email.adapter.send_mail")
    @patch("core.email.adapter.render_to_string")
    @patch("core.email.adapter.strip_tags")
    def test_send_email(self, mock_strip_tags, mock_render, mock_send_mail):
        """Test EmailAdapter.send_email method"""
        mock_render.return_value = "<html>Test Email</html>"
        mock_strip_tags.return_value = "Test Email"

        EmailAdapter.send_email(
            subject="Test Subject",
            template_name="core/emails/test.html",
            recipient_list=["test@example.com"],
            context={"name": "Test User"},
        )

        # Verify render_to_string was called with correct template and context
        mock_render.assert_called_once_with(
            "core/emails/test.html", {"name": "Test User"}
        )

        # Verify send_mail was called with correct parameters
        # In non-prod environments, emails are redirected to DEFAULT_TO_EMAIL
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        self.assertEqual(call_args[1]["subject"], "Test Subject")
        self.assertEqual(call_args[1]["from_email"], "noreply@test.com")
        self.assertEqual(call_args[1]["recipient_list"], ["test@crewii.com"])
        self.assertEqual(call_args[1]["html_message"], "<html>Test Email</html>")
        self.assertEqual(call_args[1]["message"], "Test Email")

    @override_settings(
        DEFAULT_FROM_EMAIL="noreply@test.com",
        ENV="dev",
        DEFAULT_TO_EMAIL="redirect@test.com",
        EMAIL_DEFAULT_PLATFORM="sentinel",
    )
    @patch("core.email.adapter.send_mail")
    @patch("core.email.adapter.render_to_string")
    @patch("core.email.adapter.strip_tags")
    def test_send_email_non_prod_redirects(self, mock_strip_tags, mock_render, mock_send_mail):
        """Test that emails are redirected to DEFAULT_TO_EMAIL in non-prod environments"""
        mock_render.return_value = "<html>Test Email</html>"
        mock_strip_tags.return_value = "Test Email"

        EmailAdapter.send_email(
            subject="Test Subject",
            template_name="core/emails/test.html",
            recipient_list=["test@example.com", "another@example.com"],
            context={},
        )

        # Verify recipient_list was changed to DEFAULT_TO_EMAIL in non-prod
        call_args = mock_send_mail.call_args
        self.assertEqual(call_args[1]["recipient_list"], ["redirect@test.com"])

    @override_settings(
        DEFAULT_FROM_EMAIL="noreply@test.com",
        ENV="local",
        EMAIL_DEFAULT_PLATFORM="sentinel",
    )
    @patch("core.email.adapter.send_mail")
    @patch("core.email.adapter.render_to_string")
    @patch("core.email.adapter.strip_tags")
    def test_send_email_with_custom_from_email(
        self, mock_strip_tags, mock_render, mock_send_mail
    ):
        """Test send_email with custom from_email"""
        mock_render.return_value = "<html>Test Email</html>"
        mock_strip_tags.return_value = "Test Email"

        EmailAdapter.send_email(
            subject="Test Subject",
            template_name="core/emails/test.html",
            recipient_list=["test@example.com"],
            from_email="custom@test.com",
        )

        call_args = mock_send_mail.call_args
        self.assertEqual(call_args[1]["from_email"], "custom@test.com")

    @override_settings(
        DEFAULT_FROM_EMAIL="noreply@test.com",
        ENV="local",
        EMAIL_DEFAULT_PLATFORM="sentinel",
    )
    @patch("core.email.adapter.send_mail")
    @patch("core.email.adapter.render_to_string")
    @patch("core.email.adapter.strip_tags")
    def test_send_email_with_empty_context(
        self, mock_strip_tags, mock_render, mock_send_mail
    ):
        """Test send_email with None context defaults to empty dict"""
        mock_render.return_value = "<html>Test Email</html>"
        mock_strip_tags.return_value = "Test Email"

        EmailAdapter.send_email(
            subject="Test Subject",
            template_name="core/emails/test.html",
            recipient_list=["test@example.com"],
            context=None,
        )

        # Verify render_to_string was called with empty context
        mock_render.assert_called_once_with("core/emails/test.html", {})


class EmailTasksTestCase(TestCase):
    """Test cases for email tasks"""

    @override_settings(
        DEFAULT_FROM_EMAIL="noreply@test.com",
        ENV="local",
        EMAIL_DEFAULT_PLATFORM="sentinel",
    )
    @patch("core.email.tasks.EmailAdapter")
    def test_send_password_reset_email_task(self, mock_adapter):
        """Test send_password_reset_email task"""
        send_password_reset_email("John Doe", "test@example.com", "http://example.com/reset")
        
        mock_adapter.send_email.assert_called_once()
        call_args = mock_adapter.send_email.call_args
        self.assertEqual(call_args[0][0], "Password Reset")
        self.assertEqual(call_args[0][1], "core/emails/reset-password.html")
        self.assertEqual(call_args[0][2], ["test@example.com"])
        
        # Check context
        context = call_args[0][3]
        self.assertEqual(context["name"], "John Doe")
        self.assertEqual(context["url"], "http://example.com/reset")
        self.assertEqual(context["platform"], "Sentinel")

    @override_settings(
        DEFAULT_FROM_EMAIL="noreply@test.com",
        ENV="local",
        EMAIL_DEFAULT_PLATFORM="sentinel",
    )
    @patch("core.email.tasks.EmailAdapter")
    def test_send_setup_account_email_task(self, mock_adapter):
        """Test send_setup_account_email task"""
        send_setup_account_email(
            "John Doe", "Test Org", "test@example.com", "http://example.com/setup"
        )
        
        mock_adapter.send_email.assert_called_once()
        call_args = mock_adapter.send_email.call_args
        # org_name.capitalize() only capitalizes first letter, so "Test org" -> "Test org"
        self.assertEqual(call_args[0][0], "Welcome to Test org!")
        self.assertEqual(call_args[0][1], "core/emails/setup-account.html")
        self.assertEqual(call_args[0][2], ["test@example.com"])
        
        # Check context
        context = call_args[0][3]
        self.assertEqual(context["name"], "John Doe")
        self.assertEqual(context["org_name"], "Test org")
        self.assertEqual(context["url"], "http://example.com/setup")
        self.assertEqual(context["platform"], "Sentinel")

    @override_settings(
        DEFAULT_FROM_EMAIL="noreply@test.com",
        ENV="local",
        EMAIL_DEFAULT_PLATFORM="sentinel",
    )
    @patch("core.email.tasks.EmailAdapter")
    def test_send_welcome_email_task(self, mock_adapter):
        """Test send_welcome_email task"""
        send_welcome_email(
            "John Doe", "Test Org", "test@example.com", "http://example.com/welcome"
        )
        
        mock_adapter.send_email.assert_called_once()
        call_args = mock_adapter.send_email.call_args
        # org_name.capitalize() only capitalizes first letter, so "Test org" -> "Test org"
        self.assertEqual(call_args[0][0], "Welcome to Test org!")
        self.assertEqual(call_args[0][1], "core/emails/welcome.html")
        self.assertEqual(call_args[0][2], ["test@example.com"])
        
        # Check context
        context = call_args[0][3]
        self.assertEqual(context["name"], "John Doe")
        self.assertEqual(context["org_name"], "Test org")
        self.assertEqual(context["url"], "http://example.com/welcome")
        self.assertEqual(context["platform"], "Sentinel")

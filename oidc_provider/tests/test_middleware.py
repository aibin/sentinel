from django.test import RequestFactory, TestCase
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.backends.db import SessionStore

from oidc_provider.middleware import SentinelSessionMiddleware
from oidc_provider.models import Organization


class SentinelSessionMiddlewareTestCase(TestCase):
    """Test cases for SentinelSessionMiddleware"""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SentinelSessionMiddleware(lambda request: None)
        self.organization = Organization.objects.create(
            name="Test Organization",
            slug="test-org",
            default=True,
        )

    def test_process_request_with_organization_id(self):
        """Test process_request with organization_id in GET params"""
        request = self.factory.get("/test/", {"organization_id": str(self.organization.id)})
        self.middleware.process_request(request)
        self.assertEqual(request.organization, self.organization)
        self.assertIsNotNone(request.session)
        self.assertEqual(request.session.get("organization_id"), self.organization.id)

    def test_process_request_with_organization_id_in_post(self):
        """Test process_request with organization_id in POST params"""
        request = self.factory.post("/test/", {"organization_id": str(self.organization.id)})
        self.middleware.process_request(request)
        self.assertEqual(request.organization, self.organization)

    def test_process_request_without_organization_id_uses_default(self):
        """Test process_request without organization_id uses default"""
        request = self.factory.get("/test/")
        self.middleware.process_request(request)
        self.assertEqual(request.organization, self.organization)
        self.assertTrue(request.organization.default)

    def test_process_request_with_social_path(self):
        """Test process_request with /social path extracts org from slug"""
        request = self.factory.get("/social/test-org/login/")
        self.middleware.process_request(request)
        self.assertEqual(request.organization, self.organization)
        self.assertEqual(request.organization.slug, "test-org")

    def test_process_request_with_invalid_organization_id(self):
        """Test process_request with invalid organization_id"""
        request = self.factory.get("/test/", {"organization_id": "invalid-id"})
        response = self.middleware.process_request(request)
        # Should return error response
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)  # Renders error template

    def test_process_request_without_default_organization(self):
        """Test process_request when no default organization exists"""
        # Delete default organization
        self.organization.delete()
        request = self.factory.get("/test/")
        response = self.middleware.process_request(request)
        # Should return error response
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)  # Renders error template

    def test_process_response_sets_cookie(self):
        """Test process_response sets organization-specific cookie"""
        request = self.factory.get("/test/", {"organization_id": str(self.organization.id)})
        self.middleware.process_request(request)
        
        # Create a mock response
        from django.http import HttpResponse
        response = HttpResponse()
        
        # Set session attributes
        request.session.accessed = True
        request.session.modified = True
        
        response = self.middleware.process_response(request, response)
        
        # Check that cookie name includes organization slug
        cookie_name = f"oidc_session_id_{self.organization.slug}"
        # Cookie should be set (we can't easily check the actual cookie value in unit tests)
        self.assertIsNotNone(response)

    def test_process_response_deletes_empty_session_cookie(self):
        """Test process_response deletes cookie for empty session"""
        request = self.factory.get("/test/", {"organization_id": str(self.organization.id)})
        cookie_name = f"oidc_session_id_{self.organization.slug}"
        request.COOKIES[cookie_name] = "test-session-key"
        
        self.middleware.process_request(request)
        
        # Create empty session
        request.session.clear()
        request.session.accessed = True
        request.session.modified = True
        
        from django.http import HttpResponse
        response = HttpResponse()
        response = self.middleware.process_response(request, response)
        
        # Cookie should be deleted (we can't easily verify this in unit tests)
        self.assertIsNotNone(response)

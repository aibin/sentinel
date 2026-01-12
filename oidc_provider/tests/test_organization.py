from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from oidc_provider.models import (
    Organization,
    Client,
    Connection,
    Membership,
    ResponseType,
)

User = get_user_model()


class OrganizationTestCase(TestCase):
    """Test cases for Organization model"""

    def setUp(self):
        self.org1 = Organization.objects.create(
            name="Test Organization 1",
            slug="test-org-1",
            default=True,
        )
        self.org2 = Organization.objects.create(
            name="Test Organization 2",
            slug="test-org-2",
            default=False,
        )

    def test_organization_creation(self):
        """Test creating an organization"""
        org = Organization.objects.create(
            name="New Organization",
            slug="new-org",
        )
        self.assertEqual(org.name, "New Organization")
        self.assertEqual(org.slug, "new-org")
        self.assertFalse(org.default)

    def test_organization_slug_auto_generation(self):
        """Test that slug is auto-generated from name if not provided"""
        org = Organization.objects.create(name="Auto Slug Org")
        self.assertEqual(org.slug, "auto_slug_org")

    def test_organization_slug_normalization(self):
        """Test that slug is normalized (lowercase, spaces to underscores)"""
        org = Organization.objects.create(name="Test Org", slug="  TEST-ORG  ")
        org.save()
        self.assertEqual(org.slug, "test-org")

    def test_organization_default_uniqueness(self):
        """Test that only one organization can be default"""
        # Create a new default org
        org3 = Organization.objects.create(
            name="New Default Org",
            slug="new-default",
            default=True,
        )
        # Refresh org1 from DB
        self.org1.refresh_from_db()
        # org1 should no longer be default
        self.assertFalse(self.org1.default)
        # org3 should be default
        self.assertTrue(org3.default)

    def test_organization_get_default(self):
        """Test get_default class method"""
        default_org = Organization.get_default()
        self.assertTrue(default_org.default)
        self.assertEqual(default_org, self.org1)

    def test_organization_get_all_users_default(self):
        """Test get_all_users for default organization"""
        user1 = User.objects.create_user(
            email="user1@example.com", password="pass123"
        )
        user2 = User.objects.create_user(
            email="user2@example.com", password="pass123"
        )
        # Default org should return all users
        users = self.org1.get_all_users()
        self.assertIn(user1, users)
        self.assertIn(user2, users)

    def test_organization_get_all_users_non_default(self):
        """Test get_all_users for non-default organization"""
        user1 = User.objects.create_user(
            email="user1@example.com", password="pass123"
        )
        user2 = User.objects.create_user(
            email="user2@example.com", password="pass123"
        )
        # Create membership only for user1
        Membership.objects.create(
            organization=self.org2, user=user1, active=True
        )
        # Non-default org should return only members
        users = self.org2.get_all_users()
        self.assertIn(user1, users)
        self.assertNotIn(user2, users)

    def test_organization_get_organization_user_by_email(self):
        """Test get_organization_user_by_email method"""
        user = User.objects.create_user(
            email="member@example.com", password="pass123"
        )
        membership = Membership.objects.create(
            organization=self.org2, user=user, active=True
        )
        result = self.org2.get_organization_user_by_email("member@example.com")
        self.assertEqual(result, membership)

    def test_organization_get_organization_user_by_email_not_found(self):
        """Test get_organization_user_by_email returns None for non-member"""
        User.objects.create_user(email="nonmember@example.com", password="pass123")
        result = self.org2.get_organization_user_by_email("nonmember@example.com")
        self.assertIsNone(result)

    def test_organization_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.org1), "Test Organization 1")


class ClientTestCase(TestCase):
    """Test cases for Client model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com", password="pass123"
        )
        self.response_type = ResponseType.objects.create(
            value="code", description="Authorization Code Flow"
        )

    def test_client_creation(self):
        """Test creating a client"""
        client = Client.objects.create(
            name="Test Client",
            client_type="confidential",
            jwt_alg="RS256",
        )
        client.response_types.add(self.response_type)
        self.assertEqual(client.name, "Test Client")
        self.assertEqual(client.client_type, "confidential")
        self.assertEqual(client.jwt_alg, "RS256")
        self.assertIn(self.response_type, client.response_types.all())

    def test_client_redirect_uris_property(self):
        """Test redirect_uris property"""
        client = Client.objects.create(name="Test Client")
        client.redirect_uris = ["http://example.com/callback", "http://example.com/callback2"]
        client.save()
        self.assertEqual(
            client.redirect_uris, ["http://example.com/callback", "http://example.com/callback2"]
        )

    def test_client_post_logout_redirect_uris_property(self):
        """Test post_logout_redirect_uris property"""
        client = Client.objects.create(name="Test Client")
        client.post_logout_redirect_uris = ["http://example.com/logout"]
        client.save()
        self.assertEqual(client.post_logout_redirect_uris, ["http://example.com/logout"])

    def test_client_scope_property(self):
        """Test scope property"""
        client = Client.objects.create(name="Test Client")
        client.scope = ["openid", "profile", "email"]
        client.save()
        self.assertEqual(client.scope, ["openid", "profile", "email"])

    def test_client_default_redirect_uri(self):
        """Test default_redirect_uri property"""
        client = Client.objects.create(name="Test Client")
        client.redirect_uris = ["http://example.com/callback"]
        self.assertEqual(client.default_redirect_uri, "http://example.com/callback")

    def test_client_default_redirect_uri_empty(self):
        """Test default_redirect_uri returns empty string when no URIs"""
        client = Client.objects.create(name="Test Client")
        self.assertEqual(client.default_redirect_uri, "")

    def test_client_response_type_values(self):
        """Test response_type_values method"""
        client = Client.objects.create(name="Test Client")
        client.response_types.add(self.response_type)
        values = list(client.response_type_values())
        self.assertIn("code", values)

    def test_client_str_representation(self):
        """Test string representation"""
        client = Client.objects.create(name="Test Client")
        self.assertEqual(str(client), "Test Client")


class ConnectionTestCase(TestCase):
    """Test cases for Connection model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com", password="pass123"
        )
        self.organization = Organization.objects.create(
            name="Test Org", slug="test-org", default=True
        )
        self.client = Client.objects.create(name="Test Client")
        self.response_type = ResponseType.objects.create(
            value="code", description="Authorization Code Flow"
        )
        self.client.response_types.add(self.response_type)

    def test_connection_creation(self):
        """Test creating a connection"""
        connection = Connection.objects.create(
            client=self.client,
            organization=self.organization,
            allow_registration=True,
        )
        self.assertEqual(connection.client, self.client)
        self.assertEqual(connection.organization, self.organization)
        self.assertTrue(connection.allow_registration)

    def test_connection_str_representation(self):
        """Test string representation"""
        connection = Connection.objects.create(
            client=self.client,
            organization=self.organization,
        )
        self.assertIn(str(self.client), str(connection))
        self.assertIn(str(self.organization), str(connection))


class MembershipTestCase(TestCase):
    """Test cases for Membership model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="pass123"
        )
        self.organization = Organization.objects.create(
            name="Test Org", slug="test-org", default=True
        )
        self.role = Group.objects.create(name="admin")

    def test_membership_creation(self):
        """Test creating a membership"""
        membership = Membership.objects.create(
            organization=self.organization,
            user=self.user,
            active=True,
        )
        self.assertEqual(membership.organization, self.organization)
        self.assertEqual(membership.user, self.user)
        self.assertTrue(membership.active)

    def test_membership_with_roles(self):
        """Test membership with roles"""
        membership = Membership.objects.create(
            organization=self.organization,
            user=self.user,
            active=True,
        )
        membership.roles.add(self.role)
        self.assertIn(self.role, membership.roles.all())

    def test_membership_unique_together(self):
        """Test that user can only have one membership per organization"""
        Membership.objects.create(
            organization=self.organization,
            user=self.user,
            active=True,
        )
        # Try to create duplicate membership
        with self.assertRaises(Exception):  # IntegrityError or similar
            Membership.objects.create(
                organization=self.organization,
                user=self.user,
                active=True,
            )

    def test_membership_str_representation(self):
        """Test string representation"""
        membership = Membership.objects.create(
            organization=self.organization,
            user=self.user,
            active=True,
        )
        self.assertIn(str(self.organization), str(membership))
        self.assertIn(str(self.user), str(membership))


class ResponseTypeTestCase(TestCase):
    """Test cases for ResponseType model"""

    def test_response_type_creation(self):
        """Test creating a response type"""
        response_type = ResponseType.objects.create(
            value="code",
            description="Authorization Code Flow",
        )
        self.assertEqual(response_type.value, "code")
        self.assertEqual(response_type.description, "Authorization Code Flow")

    def test_response_type_natural_key(self):
        """Test natural key method"""
        response_type = ResponseType.objects.create(
            value="code",
            description="Authorization Code Flow",
        )
        self.assertEqual(response_type.natural_key(), ("code",))

    def test_response_type_get_by_natural_key(self):
        """Test get_by_natural_key manager method"""
        ResponseType.objects.create(
            value="code",
            description="Authorization Code Flow",
        )
        response_type = ResponseType.objects.get_by_natural_key("code")
        self.assertEqual(response_type.value, "code")

    def test_response_type_str_representation(self):
        """Test string representation"""
        response_type = ResponseType.objects.create(
            value="code",
            description="Authorization Code Flow",
        )
        self.assertEqual(str(response_type), "Authorization Code Flow")


class OrganizationUserRolesTestCase(TestCase):
    """Test cases for organization user roles functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="pass123"
        )
        self.organization = Organization.objects.create(
            name="Test Org", slug="test-org", default=False
        )
        self.client = Client.objects.create(name="Test Client")
        self.connection = Connection.objects.create(
            client=self.client,
            organization=self.organization,
        )
        self.membership = Membership.objects.create(
            organization=self.organization,
            user=self.user,
            active=True,
        )
        self.group1 = Group.objects.create(name="admin")
        self.group2 = Group.objects.create(name="user")
        self.membership_role = Group.objects.create(name="member")

    def test_get_userroles_for_client_default_org(self):
        """Test get_userroles_for_client for default organization"""
        default_org = Organization.objects.create(
            name="Default Org", slug="default-org", default=True
        )
        self.user.groups.add(self.group1)
        roles = default_org.get_userroles_for_client(self.user, self.client)
        self.assertIn(self.group1, roles)

    def test_get_userroles_for_client_with_connection_grants(self):
        """Test get_userroles_for_client with connection grants"""
        # Add grants to connection
        self.connection.grants.add(self.group1)
        # Add role to membership
        self.membership.roles.add(self.membership_role)
        # Add group to user
        self.user.groups.add(self.group2)

        roles = self.organization.get_userroles_for_client(self.user, self.client)
        # Should only return roles that are in both user_roles and connection_grants
        # Since group1 is in connection grants but not in user roles, it shouldn't be returned
        # Since membership_role is in user roles but not in connection grants, it shouldn't be returned
        # Since group2 is in user groups but not in connection grants, it shouldn't be returned
        self.assertEqual(len(roles), 0)

    def test_get_userroles_for_client_matching_grants(self):
        """Test get_userroles_for_client when user roles match connection grants"""
        # Add same group to connection grants and user groups
        self.connection.grants.add(self.group1)
        self.user.groups.add(self.group1)
        roles = self.organization.get_userroles_for_client(self.user, self.client)
        self.assertIn(self.group1, roles)

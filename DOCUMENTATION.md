# Sentinel - OpenID Connect Provider

## Documentation

### Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
   - [Configuration](#configuration)
3. [Core Concepts](#core-concepts)
   - [Organizations](#organizations)
   - [Clients](#clients)
   - [Users and Authentication](#users-and-authentication)
   - [Identity Providers](#identity-providers)
4. [Administration](#administration)
   - [Creating Organizations](#creating-organizations)
   - [Managing Clients](#managing-clients)
   - [User Management](#user-management)
   - [Identity Provider Setup](#identity-provider-setup)
5. [API Reference](#api-reference)
   - [Authentication](#authentication)
   - [User Management APIs](#user-management-apis)
   - [Organization Management APIs](#organization-management-apis)
6. [Developer Guide](#developer-guide)
   - [Project Structure](#project-structure)
   - [Extending Sentinel](#extending-sentinel)
   - [Custom Claims and Scopes](#custom-claims-and-scopes)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

## Introduction

Sentinel is a Django-based OpenID Connect (OIDC) provider designed to offer secure authentication and authorization services. It serves as a centralized identity provider that can be used by multiple applications (clients) to authenticate users and grant access to protected resources.

Key features include:
- Full OpenID Connect protocol support
- Multi-tenant architecture with organization-based separation
- Social authentication integration (Google, Microsoft)
- Customizable user consent screens
- JWT-based tokens with RSA or HMAC signatures
- API for user and organization management

## Getting Started

### Prerequisites

Before installing Sentinel, ensure you have the following:

- Python 3.8 or higher
- pip and pipenv
- PostgreSQL (recommended for production) or SQLite
- Redis (for Celery tasks)

### Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/yourusername/sentinel.git
   cd sentinel
   ```

2. **Install dependencies**:
   ```sh
   pipenv install
   pipenv shell
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root with the following variables:
   ```
   SECRET_KEY=your-secure-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1
   DATABASE_URL=postgres://user:password@localhost:5432/sentinel
   DEFAULT_ORG_NAME=Your Organization
   DEFAULT_FROM_EMAIL=noreply@your-domain.com
   SENDGRID_API_KEY=your-sendgrid-api-key
   ```

4. **Initialize the database**:
   ```sh
   ./manage.py migrate
   ```

5. **Create necessary keys and initial setup**:
   ```sh
   ./manage.py creatersakey
   ./manage.py createorganization
   ./manage.py createresponsetypes
   ./manage.py createmgmttoken
   ./manage.py createsuperuser
   ./manage.py creategroups
   ```

6. **Collect static files**:
   ```sh
   ./manage.py collectstatic
   ```

7. **Start the development server**:
   ```sh
   ./manage.py runserver
   ```

### Configuration

Sentinel's configuration is managed through Django settings. Key settings specific to Sentinel include:

- **DEFAULT_ORG_NAME**: Default organization name for initial setup
- **DEFAULT_LOGIN_FIELD**: Field used for login (email or username)
- **OIDC_MANAGEMENT_TOKEN_SIGNATURE_EXPIRE**: Expiration time (in seconds) for management tokens

For production deployment, make sure to:
1. Set `DEBUG=False`
2. Configure a proper database
3. Set up HTTPS with proper certificates
4. Configure email settings for notifications
5. Set a strong SECRET_KEY

## Core Concepts

### Organizations

Organizations are the top-level entities in Sentinel that represent tenants in the multi-tenant architecture. Each organization:
- Has its own set of users
- Can have multiple OIDC clients
- Can configure its own identity providers
- May have custom branding and settings

### Clients

Clients represent applications that use Sentinel for authentication. Each client:
- Has a unique client ID and secret
- Is associated with one or more organizations
- Has defined redirect URIs
- Specifies which OIDC flows and scopes it supports
- Can have custom settings for consent

### Users and Authentication

Users in Sentinel:
- Belong to one or more organizations
- Can authenticate with username/password or social providers
- Have profile information that can be shared with clients
- Can provide consent for specific scopes requested by clients

### Identity Providers

Identity providers allow users to authenticate with external services:
- Social providers like Google and Microsoft
- Custom SAML or OAuth providers
- Each provider can be configured at the organization level

## Administration

### Creating Organizations

To create a new organization:

1. Use the Django admin interface (`/admin/oidc_provider/organization/add/`)
2. Provide a name and slug for the organization
3. Configure organization-specific settings like login page customization
4. Save the organization

Alternatively, use the management command:
```sh
./manage.py createorganization --name "Your Organization" --slug your-org
```

### Managing Clients

To create and configure a client:

1. Navigate to the Django admin interface (`/admin/oidc_provider/client/add/`)
2. Fill in the client details:
   - Name
   - Client type (confidential or public)
   - Allowed response types
   - Redirect URIs
   - Scopes
   - JWT algorithm
3. Configure consent settings
4. Associate the client with organizations

### User Management

Users can be managed through:

1. **Django Admin**:
   - Navigate to `/admin/core/user/`
   - Create, edit, or delete users
   - Manage user organization memberships

2. **API**:
   - Use the user management API endpoints
   - Authenticate with management tokens

3. **Management Commands**:
   ```sh
   ./manage.py createuser --email user@example.com --org your-org
   ```

### Identity Provider Setup

To configure a social identity provider:

1. Create a project in the provider's developer console (Google, Microsoft, etc.)
2. Get the client ID and secret
3. In Sentinel admin, create a new Identity Provider record
4. Associate the provider with the appropriate organization
5. Configure the redirect URI in the provider's console to point to Sentinel

## API Reference

### Authentication

API authentication uses token-based authentication:

```http
POST /api/v1/token/
Content-Type: application/json

{
  "client_id": "your-client-id",
  "client_secret": "your-client-secret"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

For API requests, include the token in the Authorization header:
```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

### User Management APIs

**Create User**:
```http
POST /api/v1/organization/user/
Authorization: Bearer [token]
Content-Type: application/json

{
  "email": "newuser@example.com",
  "first_name": "New",
  "last_name": "User",
  "organization_id": "org-id"
}
```

**Update User**:
```http
PUT /api/v1/organization/user/{user_id}/
Authorization: Bearer [token]
Content-Type: application/json

{
  "first_name": "Updated",
  "last_name": "User"
}
```

### Organization Management APIs

*Note: These endpoints may need to be implemented as they currently appear limited in the project.*

## Developer Guide

### Project Structure

Sentinel is organized into several Django apps:

- **core**: Base user models, authentication views
- **oidc_provider**: OIDC protocol implementation
- **social_django**: Social authentication integration

Key files and directories:
- `sentinel/settings.py`: Main Django settings
- `oidc_provider/models.py`: OIDC-related data models
- `core/models.py`: User and authentication models
- `oidc_provider/views.py`: OIDC endpoint implementations

### Extending Sentinel

To extend Sentinel with custom functionality:

1. **Custom Claims**:
   Create a custom claims class by extending `StandardScopeClaims` and register it in settings.

2. **Custom Authentication Flow**:
   Implement custom middleware or authentication backends.

3. **Additional APIs**:
   Add new views and URL routes for additional functionality.

### Custom Claims and Scopes

To add custom claims:

1. Create a class that extends `StandardScopeClaims`:
   ```python
   from oidc_provider.lib.claims import StandardScopeClaims

   class CustomClaims(StandardScopeClaims):
       def scope_custom(self):
           return {
               "custom_field": self.user.custom_field,
           }
   ```

2. Register it in settings:
   ```python
   OIDC_EXTRA_SCOPE_CLAIMS = "yourapp.claims.CustomClaims"
   ```

## Troubleshooting

### Common Issues

**Issue**: Token validation fails
**Solution**: Check that RSA keys are properly generated and that the client is using the correct public key.

**Issue**: Login redirects are not working
**Solution**: Verify that the client's redirect URIs are properly configured and that the ALLOWED_HOSTS setting includes all necessary domains.

**Issue**: Email notifications not sending
**Solution**: Check email service configuration (SendGrid API key, etc.) and verify that Celery is running.

**Issue**: Social login fails
**Solution**: Verify that the social provider is properly configured in both Sentinel and the provider's developer console.

## FAQ

**Q: Can Sentinel support multiple organizations with different branding?**
A: Yes, each organization can have its own branding settings, including logos and color schemes.

**Q: Is it possible to add custom authentication methods?**
A: Yes, you can implement custom authentication backends in Django and integrate them with Sentinel.

**Q: How do I rotate RSA keys without disrupting service?**
A: Use the management command `./manage.py creatersakey` to create a new key, and then gradually transition clients to use the new key.

**Q: Can users belong to multiple organizations?**
A: Yes, users can be members of multiple organizations, with different roles in each.

**Q: How do I implement MFA (Multi-Factor Authentication)?**
A: Sentinel includes integration with Django Two-Factor, which can be configured in the settings. 
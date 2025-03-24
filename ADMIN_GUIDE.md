# Sentinel - Administrator Guide

This guide is intended for administrators who need to set up, configure, and manage Sentinel, the OpenID Connect (OIDC) provider.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
   - [System Requirements](#system-requirements)
   - [Deployment Options](#deployment-options)
   - [Environment Configuration](#environment-configuration)
3. [Initial Setup](#initial-setup)
   - [Creating the First Organization](#creating-the-first-organization)
   - [Setting Up Administrator Accounts](#setting-up-administrator-accounts)
   - [Generating RSA Keys](#generating-rsa-keys)
4. [Organization Management](#organization-management)
   - [Creating Organizations](#creating-organizations)
   - [Organization Settings](#organization-settings)
   - [Branding Customization](#branding-customization)
5. [Client Management](#client-management)
   - [Creating Clients](#creating-clients)
   - [Configuring Client Settings](#configuring-client-settings)
   - [Managing Client Secrets](#managing-client-secrets)
6. [User Management](#user-management)
   - [Creating and Inviting Users](#creating-and-inviting-users)
   - [User Roles and Permissions](#user-roles-and-permissions)
   - [Bulk User Operations](#bulk-user-operations)
7. [Identity Provider Configuration](#identity-provider-configuration)
   - [Setting Up Google Login](#setting-up-google-login)
   - [Setting Up Microsoft Login](#setting-up-microsoft-login)
   - [Custom Identity Providers](#custom-identity-providers)
8. [Security Settings](#security-settings)
   - [Password Policies](#password-policies)
   - [Multi-Factor Authentication](#multi-factor-authentication)
   - [Brute Force Protection](#brute-force-protection)
   - [Token Lifetime Management](#token-lifetime-management)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)
   - [Logging and Auditing](#logging-and-auditing)
   - [Backup and Recovery](#backup-and-recovery)
   - [Database Maintenance](#database-maintenance)
10. [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
    - [Diagnostic Tools](#diagnostic-tools)
    - [Support Resources](#support-resources)

## Introduction

Sentinel is a Django-based OpenID Connect (OIDC) provider designed to offer secure authentication and authorization services. As an administrator, you'll be responsible for setting up organizations, managing clients, configuring identity providers, and ensuring the system runs smoothly.

## Installation

### System Requirements

- **Operating System**: Linux (recommended), macOS, or Windows
- **Python**: 3.8 or higher
- **Database**: PostgreSQL (recommended), MySQL, or SQLite (for development only)
- **Redis**: For Celery task queue
- **Web Server**: Nginx (recommended) or Apache
- **WSGI Server**: Gunicorn, uWSGI, or similar

### Deployment Options

1. **Docker Deployment**:
   
   The simplest way to deploy Sentinel is using Docker and Docker Compose.

   ```sh
   # Clone the repository
   git clone https://github.com/yourusername/sentinel.git
   cd sentinel
   
   # Configure environment variables
   cp .env.example .env
   # Edit .env with your configuration
   
   # Start with Docker Compose
   docker-compose up -d
   ```

2. **Traditional Deployment**:

   ```sh
   # Clone the repository
   git clone https://github.com/yourusername/sentinel.git
   cd sentinel
   
   # Create a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pipenv install
   
   # Configure environment variables
   cp .env.example .env
   # Edit .env with your configuration
   
   # Run migrations
   ./manage.py migrate
   
   # Create initial setup
   ./manage.py creatersakey
   ./manage.py createorganization
   ./manage.py createresponsetypes
   ./manage.py createmgmttoken
   ./manage.py createsuperuser
   ./manage.py creategroups
   
   # Collect static files
   ./manage.py collectstatic --no-input
   ```

### Environment Configuration

Key environment variables to configure:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key (keep this secure) | `YOUR_SECURE_RANDOM_KEY` |
| `DEBUG` | Debug mode (False in production) | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `sentinel.example.com,localhost` |
| `DATABASE_URL` | Database connection URL | `postgres://user:password@localhost/sentinel` |
| `DEFAULT_ORG_NAME` | Default organization name | `My Organization` |
| `DEFAULT_FROM_EMAIL` | Default sender email address | `noreply@example.com` |
| `SENDGRID_API_KEY` | SendGrid API key for email delivery | `SG.your-key` |
| `CELERY_BROKER_URL` | Redis URL for Celery | `redis://localhost:6379/0` |

## Initial Setup

### Creating the First Organization

After installation, create your first organization:

```sh
./manage.py createorganization --name "Your Organization" --slug your-org
```

This creates the primary organization in Sentinel.

### Setting Up Administrator Accounts

Create an admin user:

```sh
./manage.py createsuperuser
```

Follow the prompts to create your admin account.

### Generating RSA Keys

Generate RSA keys for token signing:

```sh
./manage.py creatersakey
```

This creates the necessary keys for JWT signing.

## Organization Management

### Creating Organizations

Organizations are the top-level entities in Sentinel that represent tenants.

To create a new organization:

1. Through the Django admin interface:
   - Navigate to `/admin/oidc_provider/organization/add/`
   - Fill in the organization details
   - Click "Save"

2. Using the management command:
   ```sh
   ./manage.py createorganization --name "Second Organization" --slug second-org
   ```

### Organization Settings

Key organization settings include:

- **Name**: Display name for the organization
- **Slug**: URL-friendly identifier (used in URLs)
- **Login URL**: Custom login page URL (optional)
- **Logo**: Organization logo for branding
- **Domain**: Email domain(s) associated with the organization
- **Settings**:
  - Password policies
  - Session timeouts
  - Login page customization

### Branding Customization

Customize the login experience for each organization:

1. Navigate to the organization in the admin interface
2. Upload a logo image
3. Configure custom CSS (if supported)
4. Set organization-specific email templates

## Client Management

### Creating Clients

Clients represent applications that use Sentinel for authentication.

To create a new client:

1. Navigate to `/admin/oidc_provider/client/add/`
2. Fill in the client details:
   - **Name**: Client application name
   - **Client Type**: Confidential (can securely store secrets) or Public
   - **Response Types**: Allowed OIDC flows (e.g., code, id_token, token)
   - **JWT Algorithm**: Algorithm for token signing (RS256 recommended)
   - **Redirect URIs**: Authorized callback URLs (one per line)
   - **Post-Logout Redirect URIs**: URLs to redirect after logout
   - **Scopes**: Allowed scopes (space separated)
3. Associate with organizations
4. Configure consent settings
5. Click "Save"

### Configuring Client Settings

Important client settings:

- **Reuse Consent**: If enabled, users won't be prompted for consent after the first authorization
- **Require Consent**: If disabled, consent screens are skipped entirely
- **Allow Registration**: If enabled, new users can register during authentication
- **Client Secret**: Automatically generated for confidential clients

### Managing Client Secrets

For confidential clients, you may need to manage client secrets:

1. To view or reset a client secret, navigate to the client in the admin interface
2. Look for the Client SECRET field
3. To generate a new secret, clear the field and save (a new secret will be generated)
4. Provide the new secret to the client application owner securely

## User Management

### Creating and Inviting Users

To create users:

1. Through the admin interface:
   - Navigate to `/admin/core/user/add/`
   - Fill in user details
   - Associate with organizations

2. Via management command:
   ```sh
   ./manage.py createuser --email user@example.com --first-name John --last-name Doe --org your-org
   ```

3. Using the API:
   ```http
   POST /api/v1/organization/user/
   Authorization: Bearer YOUR_MANAGEMENT_TOKEN
   Content-Type: application/json
   
   {
     "email": "user@example.com",
     "first_name": "John",
     "last_name": "Doe",
     "organization_id": "your-org-id"
   }
   ```

When a user is created, a password setup email is sent automatically.

### User Roles and Permissions

Manage user roles and permissions:

1. Navigate to the user in the admin interface
2. Assign groups (e.g., "admin", "user")
3. Set specific permissions as needed

### Bulk User Operations

For bulk operations:

1. Use the Django admin interface for bulk actions
2. Create a CSV import script for batch processing
3. Use the API with automation scripts

## Identity Provider Configuration

### Setting Up Google Login

To enable Google authentication:

1. Create a project in the Google Developer Console
2. Configure OAuth consent screen
3. Create OAuth credentials (Web application type)
4. Add authorized redirect URIs (format: `https://your-sentinel-domain.com/social/{org_slug}/complete/google-oauth2/`)
5. In Sentinel admin, create a new Identity Provider:
   - Type: Google OAuth2
   - Client ID: from Google OAuth credentials
   - Client Secret: from Google OAuth credentials
   - Organization: select the organization
6. Save the provider

### Setting Up Microsoft Login

To enable Microsoft authentication:

1. Register an application in the Azure AD portal
2. Configure platform settings (Web)
3. Add redirect URIs (format: `https://your-sentinel-domain.com/social/{org_slug}/complete/microsoft-graph/`)
4. Create a client secret
5. In Sentinel admin, create a new Identity Provider:
   - Type: Microsoft Graph
   - Client ID: from Azure app registration
   - Client Secret: from Azure client secret
   - Organization: select the organization
6. Save the provider

### Custom Identity Providers

For custom identity providers:

1. Implement the provider integration code
2. Register the new provider in settings
3. Configure in the admin interface

## Security Settings

### Password Policies

Configure password policies at the organization level:

- Minimum length
- Complexity requirements
- Password expiration
- History requirements

### Multi-Factor Authentication

Enable MFA:

1. Install the required MFA packages
2. Configure MFA settings in Django settings
3. Enable MFA for specific organizations or users

### Brute Force Protection

Sentinel uses `django-axes` for brute force protection. Configure in settings:

- Maximum login attempts (`AXES_FAILURE_LIMIT`)
- Lockout period
- Lockout method

### Token Lifetime Management

Configure token lifetimes:

- Access token expiration
- Refresh token expiration
- ID token expiration

## Monitoring and Maintenance

### Logging and Auditing

Sentinel logs important events:

- Authentication attempts
- Consent decisions
- Token issuance
- Administrative actions

Configure logging in Django settings to capture these events.

### Backup and Recovery

Regular backups are essential:

1. Database backups:
   ```sh
   pg_dump -U postgres sentinel > sentinel_backup.sql
   ```

2. RSA keys backup:
   Ensure you have secure backups of your RSA keys.

3. Environment configuration backup:
   Keep a secure copy of your `.env` file.

### Database Maintenance

Regular database maintenance:

1. Run Django's database cleanup commands:
   ```sh
   ./manage.py cleartokens  # Clear expired tokens
   ```

2. Database optimization:
   ```sh
   # For PostgreSQL
   VACUUM ANALYZE;
   ```

## Troubleshooting

### Common Issues

**Issue**: Users can't log in
**Solution**: Check user accounts are active, email verified, and organization membership is valid.

**Issue**: Client authentication fails
**Solution**: Verify client ID and secret, check redirect URIs match exactly.

**Issue**: Social login doesn't work
**Solution**: Verify identity provider configuration, check redirect URIs in both Sentinel and the provider console.

**Issue**: RSA key issues
**Solution**: Regenerate RSA keys using the management command.

### Diagnostic Tools

1. Django shell:
   ```sh
   ./manage.py shell
   ```

2. Check logs:
   ```sh
   tail -f logs/sentinel.log
   ```

3. Test email delivery:
   ```sh
   ./manage.py sendtestemail admin@example.com
   ```

### Support Resources

- Check the Sentinel documentation
- Examine Django and OIDC-related logs
- Contact the development team

## Management Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `creatersakey` | Creates RSA keys for JWT signing | `./manage.py creatersakey` |
| `createorganization` | Creates a new organization | `./manage.py createorganization --name "Org Name" --slug org-slug` |
| `createresponsetypes` | Creates OIDC response types | `./manage.py createresponsetypes` |
| `createmgmttoken` | Creates an API management token | `./manage.py createmgmttoken` |
| `creategroups` | Creates default user groups | `./manage.py creategroups` |
| `createuser` | Creates a new user | `./manage.py createuser --email user@example.com --org org-slug` |
| `cleartokens` | Clears expired tokens | `./manage.py cleartokens` | 
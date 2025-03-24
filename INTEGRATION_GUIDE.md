# Sentinel Integration Guide

This guide provides step-by-step instructions for integrating your application with Sentinel as an OpenID Connect (OIDC) provider.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Registering Your Application](#registering-your-application)
4. [Integration Methods](#integration-methods)
   - [Authorization Code Flow](#authorization-code-flow)
   - [Implicit Flow](#implicit-flow)
   - [Hybrid Flow](#hybrid-flow)
5. [Organization-Specific Login](#organization-specific-login)
   - [Organization Context](#organization-context)
   - [Implementation Examples](#implementation-examples)
   - [Custom Branding](#custom-branding)
6. [Implementation Guides](#implementation-guides)
   - [Web Applications](#web-applications)
   - [Single Page Applications](#single-page-applications)
   - [Mobile Applications](#mobile-applications)
   - [Backend APIs](#backend-apis)
7. [Token Handling](#token-handling)
8. [User Information](#user-information)
9. [Logout](#logout)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

## Overview

Sentinel is an OpenID Connect provider that allows you to delegate authentication and authorization to a central service. By integrating with Sentinel, your application can:

- Provide secure authentication without managing user credentials
- Access standardized user profile information
- Support social login providers
- Implement single sign-on across multiple applications

## Prerequisites

Before integrating with Sentinel, ensure you have:

1. Access to a Sentinel instance
2. Administrator privileges to register a client application
3. Basic understanding of OAuth 2.0 and OpenID Connect protocols

## Registering Your Application

To use Sentinel as an identity provider, you must first register your application:

1. Contact the Sentinel administrator or use the self-service portal
2. Provide the following information:
   - Application name
   - Redirect URIs (where users will be sent after authentication)
   - Type of application (web, mobile, SPA)
   - Required scopes
3. You will receive:
   - Client ID
   - Client Secret (for confidential clients)
   - Configuration information

## Integration Methods

Sentinel supports multiple OIDC flows. Choose the appropriate flow based on your application type:

### Authorization Code Flow

Best for server-side web applications where the client can securely store a client secret.

1. **Authentication Request**:
   ```
   GET /openid/authorize/?
     response_type=code&
     client_id=YOUR_CLIENT_ID&
     redirect_uri=https://your-app.com/callback&
     scope=openid profile email&
     state=RANDOM_STATE_VALUE&
     nonce=RANDOM_NONCE_VALUE
   ```

2. **Token Exchange**:
   ```
   POST /openid/token/
   Content-Type: application/x-www-form-urlencoded
   
   grant_type=authorization_code&
   code=AUTHORIZATION_CODE&
   client_id=YOUR_CLIENT_ID&
   client_secret=YOUR_CLIENT_SECRET&
   redirect_uri=https://your-app.com/callback
   ```

3. **Response**:
   ```json
   {
     "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
     "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "Bearer",
     "expires_in": 3600,
     "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
   }
   ```

### Implicit Flow

Best for browser-based applications (SPAs) that cannot securely store a client secret.

1. **Authentication Request**:
   ```
   GET /openid/authorize/?
     response_type=id_token token&
     client_id=YOUR_CLIENT_ID&
     redirect_uri=https://your-app.com/callback&
     scope=openid profile email&
     state=RANDOM_STATE_VALUE&
     nonce=RANDOM_NONCE_VALUE
   ```

2. **Response** (directly to the redirect URI as URL fragments):
   ```
   https://your-app.com/callback#
     access_token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...&
     id_token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...&
     token_type=Bearer&
     expires_in=3600&
     state=RANDOM_STATE_VALUE
   ```

### Hybrid Flow

Combines aspects of both Authorization Code and Implicit flows.

1. **Authentication Request**:
   ```
   GET /openid/authorize/?
     response_type=code id_token&
     client_id=YOUR_CLIENT_ID&
     redirect_uri=https://your-app.com/callback&
     scope=openid profile email&
     state=RANDOM_STATE_VALUE&
     nonce=RANDOM_NONCE_VALUE
   ```

2. **Response**:
   Returns both an authorization code and tokens in the redirect URI.

## Organization-Specific Login

Sentinel's multi-tenant architecture allows for organization-specific login experiences. This is particularly useful when building applications that serve multiple organizations, each with their own branding and identity providers.

### Organization Context

When redirecting users to Sentinel for authentication, you can specify which organization context to use by including the `organization_id` parameter in your authorization requests.

**Example Authorization Request with Organization ID:**
```
GET /openid/authorize/?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=https://your-app.com/callback&
  scope=openid profile email&
  state=RANDOM_STATE_VALUE&
  nonce=RANDOM_NONCE_VALUE&
  organization_id=your-organization-id
```

Alternatively, you can use the organization slug in the login URL:
```
GET /account/login/?
  organization=your-organization-slug&
  next=/openid/authorize/?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=https://your-app.com/callback&...
```

### Implementation Examples

#### 1. Web Application Organization Selection

For applications that serve multiple organizations, you might implement an organization selection screen:

**Example Organization Selection Page (Python/Django):**
```python
# views.py
from django.shortcuts import render, redirect
from django.urls import reverse
from your_app.models import Organization

def select_organization(request):
    organizations = Organization.objects.filter(active=True)
    return render(request, 'select_organization.html', {'organizations': organizations})

def login(request, org_slug):
    # Build the authorization URL with organization context
    organization = Organization.objects.get(slug=org_slug)
    
    base_url = "https://sentinel.example.com/account/login/"
    next_url = "/openid/authorize/?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=https://your-app.com/callback&scope=openid%20profile%20email&state=STATE&nonce=NONCE"
    
    login_url = f"{base_url}?organization={org_slug}&next={next_url}"
    return redirect(login_url)
```

**HTML Template (select_organization.html):**
```html
<html>
<head>
    <title>Select Your Organization</title>
    <style>
        .org-list {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        .org-card {
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 5px;
            width: 200px;
            text-align: center;
            cursor: pointer;
        }
        .org-logo {
            max-width: 150px;
            max-height: 80px;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <h1>Select Your Organization</h1>
    <div class="org-list">
        {% for org in organizations %}
            <a href="{% url 'login' org.slug %}" class="org-card">
                {% if org.logo %}
                    <img src="{{ org.logo.url }}" alt="{{ org.name }}" class="org-logo">
                {% endif %}
                <h3>{{ org.name }}</h3>
            </a>
        {% endfor %}
    </div>
</body>
</html>
```

#### 2. Organization Detection Based on Domain (JavaScript/React)

For applications that can determine the organization based on the URL or subdomain:

```jsx
import React, { useEffect } from 'react';
import { useAuth } from 'react-oidc-context';

function LoginButton() {
  const auth = useAuth();
  
  // Function to detect organization from subdomain
  const getOrganizationFromUrl = () => {
    const hostname = window.location.hostname;
    // For subdomain-based organization detection (e.g., acme.yourapp.com)
    const subdomain = hostname.split('.')[0];
    
    // Map subdomains to organization IDs or use an API call
    const orgMap = {
      'acme': 'acme-org-id',
      'globex': 'globex-org-id',
      // Add more mappings as needed
    };
    
    return orgMap[subdomain] || 'default-org-id';
  };
  
  const handleLogin = () => {
    const orgId = getOrganizationFromUrl();
    // Call signin with additional organization_id parameter
    auth.signinRedirect({
      extraQueryParams: {
        organization_id: orgId
      }
    });
  };
  
  return (
    <button onClick={handleLogin}>
      Log In with Your Organization
    </button>
  );
}
```

#### 3. Server-Side Login URL Generation (Node.js/Express)

```javascript
const express = require('express');
const router = express.Router();

// Helper function to generate Sentinel login URL
function generateSentinelLoginUrl(orgSlug, clientId, redirectUri) {
  const baseLoginUrl = 'https://sentinel.example.com/account/login/';
  const nextUrl = encodeURIComponent(`/openid/authorize/?response_type=code&client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=openid%20profile%20email&state=${generateRandomState()}&nonce=${generateRandomNonce()}`);
  
  return `${baseLoginUrl}?organization=${orgSlug}&next=${nextUrl}`;
}

// Route to handle organization-specific login
router.get('/login/:orgSlug', (req, res) => {
  const { orgSlug } = req.params;
  const clientId = process.env.SENTINEL_CLIENT_ID;
  const redirectUri = `${process.env.APP_URL}/auth/callback`;
  
  const loginUrl = generateSentinelLoginUrl(orgSlug, clientId, redirectUri);
  res.redirect(loginUrl);
});

function generateRandomState() {
  // Generate a secure random string for state parameter
  return Math.random().toString(36).substring(2, 15) + 
         Math.random().toString(36).substring(2, 15);
}

function generateRandomNonce() {
  // Generate a secure random string for nonce parameter
  return Math.random().toString(36).substring(2, 10);
}

module.exports = router;
```

### Custom Branding

Sentinel allows each organization to have custom branding elements, which are automatically applied when using organization-specific login:

1. **Organization Logo**: Displayed on the login page
2. **Custom Colors**: Organization-specific theme colors
3. **Custom Text**: Welcome messages and instructions

When implementing your application, you can also reflect this branding for a consistent user experience:

```javascript
// Example of fetching organization branding information
async function getOrganizationBranding(orgId) {
  const response = await fetch(`https://sentinel.example.com/api/v1/organization/${orgId}/branding`, {
    headers: {
      'Authorization': `Bearer ${managementToken}`
    }
  });
  
  return await response.json();
}

// Apply branding to your application
async function applyOrganizationBranding(orgId) {
  const branding = await getOrganizationBranding(orgId);
  
  // Apply primary color to CSS variables
  document.documentElement.style.setProperty('--primary-color', branding.primaryColor);
  
  // Set logo
  document.getElementById('orgLogo').src = branding.logoUrl;
  
  // Set organization name
  document.getElementById('orgName').textContent = branding.name;
}
```

## Implementation Guides

### Web Applications

For traditional web applications with server-side components:

1. **Choose a library**:
   - Node.js: [openid-client](https://github.com/panva/node-openid-client)
   - Python: [authlib](https://github.com/lepture/authlib)
   - PHP: [league/oauth2-client](https://github.com/thephpleague/oauth2-client)
   - Ruby: [omniauth-openid-connect](https://github.com/jjbohn/omniauth-openid-connect)
   - Java: [Spring Security OAuth](https://spring.io/projects/spring-security-oauth)

2. **Implementation Example (Python with Flask and Authlib)**:
   ```python
   from flask import Flask, url_for, session, redirect, request
   from authlib.integrations.flask_client import OAuth
   
   app = Flask(__name__)
   app.secret_key = 'your-secret'
   
   oauth = OAuth(app)
   oauth.register(
       name='sentinel',
       server_metadata_url='https://sentinel.example.com/openid/.well-known/openid-configuration',
       client_id='YOUR_CLIENT_ID',
       client_secret='YOUR_CLIENT_SECRET',
       client_kwargs={'scope': 'openid profile email'}
   )
   
   @app.route('/login')
   def login():
       redirect_uri = url_for('auth', _external=True)
       return oauth.sentinel.authorize_redirect(redirect_uri)
   
   @app.route('/auth')
   def auth():
       token = oauth.sentinel.authorize_access_token()
       user = oauth.sentinel.parse_id_token(token)
       session['user'] = user
       return redirect('/')
   ```

### Single Page Applications

For browser-based SPAs:

1. **Choose a library**:
   - JavaScript: [oidc-client-js](https://github.com/IdentityModel/oidc-client-js)
   - Angular: [angular-auth-oidc-client](https://github.com/damienbod/angular-auth-oidc-client)
   - React: [react-oidc-context](https://github.com/authts/react-oidc-context)

2. **Implementation Example (React with react-oidc-context)**:
   ```jsx
   import React from 'react';
   import { AuthProvider, useAuth } from 'react-oidc-context';
   
   const oidcConfig = {
     authority: "https://sentinel.example.com/openid",
     client_id: "YOUR_CLIENT_ID",
     redirect_uri: window.location.origin + "/callback",
     response_type: "code",
     scope: "openid profile email",
   };
   
   function App() {
     return (
       <AuthProvider {...oidcConfig}>
         <MainContent />
       </AuthProvider>
     );
   }
   
   function MainContent() {
     const auth = useAuth();
   
     if (auth.isLoading) {
       return <div>Loading...</div>;
     }
   
     if (auth.error) {
       return <div>Oops... {auth.error.message}</div>;
     }
   
     if (auth.isAuthenticated) {
       return (
         <div>
           Hello {auth.user?.profile.name}{" "}
           <button onClick={() => auth.signoutRedirect()}>Log out</button>
         </div>
       );
     }
   
     return <button onClick={() => auth.signinRedirect()}>Log in</button>;
   }
   ```

### Mobile Applications

For native mobile applications:

1. **Choose a library**:
   - Android: [AppAuth for Android](https://github.com/openid/AppAuth-Android)
   - iOS: [AppAuth for iOS](https://github.com/openid/AppAuth-iOS)
   - React Native: [react-native-app-auth](https://github.com/FormidableLabs/react-native-app-auth)

2. **Implementation Example (Android with AppAuth)**:
   ```java
   // Define the OIDC configuration
   AuthorizationServiceConfiguration serviceConfig = new AuthorizationServiceConfiguration(
       Uri.parse("https://sentinel.example.com/openid/authorize/"),
       Uri.parse("https://sentinel.example.com/openid/token/"),
       null,
       Uri.parse("https://sentinel.example.com/openid/revoke/")
   );
   
   // Create an authorization request
   AuthorizationRequest.Builder authRequestBuilder =
       new AuthorizationRequest.Builder(
           serviceConfig,
           YOUR_CLIENT_ID,
           ResponseTypeValues.CODE,
           Uri.parse("com.example.app:/oauth2callback")
       );
   
   AuthorizationRequest authRequest = authRequestBuilder
       .setScope("openid profile email")
       .build();
   
   // Perform the authorization request
   AuthorizationService authService = new AuthorizationService(context);
   Intent authIntent = authService.getAuthorizationRequestIntent(authRequest);
   startActivityForResult(authIntent, RC_AUTH);
   ```

### Backend APIs

For APIs that need to validate tokens:

1. **Implementation Example (Node.js with express-oauth2-jwt-bearer)**:
   ```javascript
   const express = require('express');
   const { auth } = require('express-oauth2-jwt-bearer');
   
   const app = express();
   
   // Set up JWT validation middleware
   const checkJwt = auth({
     audience: 'YOUR_API_IDENTIFIER',
     issuerBaseURL: 'https://sentinel.example.com/openid',
   });
   
   // Protected API route
   app.get('/api/protected', checkJwt, (req, res) => {
     res.json({ message: 'This is a protected API' });
   });
   
   app.listen(3000, () => {
     console.log('Server running on port 3000');
   });
   ```

## Token Handling

After obtaining tokens from Sentinel:

1. **Storing Tokens**:
   - Web apps: Store in server-side session
   - SPAs: Store in memory or secure browser storage
   - Mobile apps: Store in secure device storage

2. **Token Validation**:
   - Verify the token signature
   - Check the expiration time
   - Validate the issuer and audience
   - Verify the nonce to prevent replay attacks

3. **Token Renewal**:
   When access tokens expire, use the refresh token to get new tokens:
   ```
   POST /openid/token/
   Content-Type: application/x-www-form-urlencoded
   
   grant_type=refresh_token&
   refresh_token=YOUR_REFRESH_TOKEN&
   client_id=YOUR_CLIENT_ID&
   client_secret=YOUR_CLIENT_SECRET
   ```

## User Information

To get user profile information:

1. **Using ID Token**:
   The ID token contains basic user information in its payload.

2. **Calling the UserInfo Endpoint**:
   ```
   GET /openid/userinfo/
   Authorization: Bearer YOUR_ACCESS_TOKEN
   ```

   Response:
   ```json
   {
     "sub": "user-id",
     "name": "John Doe",
     "email": "john.doe@example.com",
     "email_verified": true
   }
   ```

## Logout

To log a user out:

1. **Local Logout**:
   - Clear tokens from your application's storage
   - Destroy the user session

2. **OIDC Logout**:
   ```
   GET /openid/end-session/?
     id_token_hint=ID_TOKEN&
     post_logout_redirect_uri=https://your-app.com/logout-success
   ```

## Best Practices

1. **Security**:
   - Always validate tokens on the server side
   - Use HTTPS for all communication
   - Implement PKCE for public clients
   - Store tokens securely

2. **Performance**:
   - Cache the OIDC configuration
   - Use silent refresh for SPAs
   - Minimize redirect times

3. **UX Considerations**:
   - Provide a seamless login experience
   - Handle errors gracefully
   - Provide clear feedback during authentication

## Troubleshooting

### Common Issues

**Issue**: Invalid redirect URI error
**Solution**: Ensure the redirect URI in your request exactly matches the one registered with Sentinel.

**Issue**: Token validation fails
**Solution**: Check that you're using the correct public key from Sentinel's JWKS endpoint.

**Issue**: "Invalid client" error
**Solution**: Verify your client ID and secret are correct.

**Issue**: Scopes not included in token
**Solution**: Ensure the requested scopes are allowed for your client in Sentinel.

### Debugging Tools

1. **OIDC Debugger**: Use [oidcdebugger.com](https://oidcdebugger.com/) to test your authorization requests.
2. **JWT Debugger**: Use [jwt.io](https://jwt.io/) to decode and inspect tokens.
3. **Network Monitoring**: Use browser developer tools to inspect network requests and responses. 
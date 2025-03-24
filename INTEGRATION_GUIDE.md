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
5. [Implementation Guides](#implementation-guides)
   - [Web Applications](#web-applications)
   - [Single Page Applications](#single-page-applications)
   - [Mobile Applications](#mobile-applications)
   - [Backend APIs](#backend-apis)
6. [Token Handling](#token-handling)
7. [User Information](#user-information)
8. [Logout](#logout)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

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
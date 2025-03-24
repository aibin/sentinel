# Sentinel Examples

This directory contains example applications and code snippets that demonstrate how to use and integrate with Sentinel.

## Organization Login Demo

The `organization_login_demo.py` file demonstrates how to implement organization-specific login in a Flask web application.

### Features

- Organization selection screen with custom branding
- Organization-specific login with Sentinel
- OIDC authentication flow
- User profile display after successful login

### How to Run

1. **Install dependencies**:

   ```
   pip install flask authlib requests
   ```

2. **Configure environment variables**:

   You can set these environment variables or edit the defaults in the code:

   ```
   export SENTINEL_BASE_URL=http://localhost:8000
   export CLIENT_ID=your-client-id
   export CLIENT_SECRET=your-client-secret
   export SECRET_KEY=make-this-random-and-secure
   ```

3. **Run the application**:

   ```
   python organization_login_demo.py
   ```

4. **Access the demo**:

   Open your browser and navigate to http://localhost:5000

### How it Works

1. The application displays a selection of organizations to choose from
2. When a user selects an organization, the application:
   - Generates a redirect URL with organization context
   - Redirects to Sentinel's login page with the organization parameter
   - Includes the authorization parameters as the "next" parameter
3. After login, Sentinel redirects back to the application's callback URL
4. The application exchanges the authorization code for tokens
5. The application retrieves and displays the user's profile information

### Key Concepts Demonstrated

- **Organization Context**: Using the `organization` parameter in login URLs
- **Authorization Flow**: Implementing the OIDC authorization code flow
- **User Profile**: Retrieving user information via the userinfo endpoint
- **Branding**: Applying organization-specific branding elements
- **Security**: Implementing state and nonce for CSRF and replay protection

### Adapting for Production

When adapting this example for production use:

1. Use a proper template system instead of template strings
2. Store sensitive configuration in environment variables or a secure configuration system
3. Implement proper error handling and logging
4. Use HTTPS for all communication
5. Implement proper session management and security
6. Add CSRF protection
7. Consider adding token refresh functionality 
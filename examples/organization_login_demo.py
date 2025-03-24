#!/usr/bin/env python
"""
Organization Login Demo

This is a simple Flask application that demonstrates how to implement
organization-specific login with Sentinel OIDC provider.

Requirements:
- Flask
- Authlib
- Requests

Install with:
pip install flask authlib requests
"""

import json
import os
from urllib.parse import urlencode

from authlib.integrations.flask_client import OAuth
from flask import (Flask, redirect, render_template, request, session, url_for,
                   jsonify)

# Configuration
SENTINEL_BASE_URL = os.environ.get('SENTINEL_BASE_URL', 'http://localhost:8000')
CLIENT_ID = os.environ.get('CLIENT_ID', 'your-client-id')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', 'your-client-secret')
SECRET_KEY = os.environ.get('SECRET_KEY', 'make-this-random-and-secure')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Configure OAuth
oauth = OAuth(app)

# Dictionary of organizations for the demo
# In a real application, you might fetch these from a database
ORGANIZATIONS = {
    'acme': {
        'name': 'ACME Corporation',
        'slug': 'acme',
        'logo': 'https://via.placeholder.com/150x50.png?text=ACME',
        'color': '#336699'
    },
    'globex': {
        'name': 'Globex Industries',
        'slug': 'globex',
        'logo': 'https://via.placeholder.com/150x50.png?text=Globex',
        'color': '#993366'
    },
    'initech': {
        'name': 'Initech Technologies',
        'slug': 'initech',
        'logo': 'https://via.placeholder.com/150x50.png?text=Initech',
        'color': '#669933'
    }
}

# HTML templates as strings for simplicity
# In a real application, use proper template files
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Organization Login Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #333;
        }
        .org-list {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-top: 30px;
        }
        .org-card {
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 5px;
            width: 200px;
            text-align: center;
            cursor: pointer;
            text-decoration: none;
            color: #333;
            transition: transform 0.2s;
        }
        .org-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .org-logo {
            max-width: 150px;
            max-height: 50px;
            margin-bottom: 10px;
        }
        .login-button {
            display: inline-block;
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            margin-top: 10px;
            border-radius: 4px;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <h1>Select Your Organization</h1>
    <p>Choose the organization you belong to:</p>
    
    <div class="org-list">
        {% for slug, org in organizations.items() %}
            <a href="{{ url_for('login', org_slug=slug) }}" class="org-card" style="border-color: {{ org.color }};">
                <img src="{{ org.logo }}" alt="{{ org.name }}" class="org-logo">
                <h3>{{ org.name }}</h3>
                <div class="login-button" style="background-color: {{ org.color }};">Login</div>
            </a>
        {% endfor %}
    </div>
</body>
</html>
'''

CALLBACK_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login Successful</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #333;
        }
        .profile {
            background-color: #f5f5f5;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
        }
        .profile-item {
            margin-bottom: 10px;
        }
        .label {
            font-weight: bold;
            display: inline-block;
            width: 150px;
        }
        .logout {
            display: inline-block;
            background-color: #f44336;
            color: white;
            padding: 10px 20px;
            margin-top: 20px;
            border-radius: 4px;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <h1>Login Successful</h1>
    
    {% if organization %}
    <p>You are logged in to <strong>{{ organization.name }}</strong>.</p>
    {% endif %}
    
    <div class="profile">
        <h2>User Profile</h2>
        {% for key, value in userinfo.items() %}
            <div class="profile-item">
                <span class="label">{{ key }}:</span>
                <span>{{ value }}</span>
            </div>
        {% endfor %}
    </div>
    
    <a href="{{ url_for('logout') }}" class="logout">Logout</a>
</body>
</html>
'''

# Routes
@app.route('/')
def index():
    """Show organization selection page"""
    return render_template_string(INDEX_TEMPLATE, organizations=ORGANIZATIONS)


@app.route('/login/<org_slug>')
def login(org_slug):
    """Handle login for a specific organization"""
    if org_slug not in ORGANIZATIONS:
        return "Organization not found", 404
    
    # Store the organization slug in session for later use
    session['org_slug'] = org_slug
    
    # Register the OAuth client dynamically with the right organization context
    sentinel_oauth = oauth.register(
        name='sentinel',
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        access_token_url=f"{SENTINEL_BASE_URL}/openid/token/",
        authorize_url=f"{SENTINEL_BASE_URL}/openid/authorize/",
        userinfo_url=f"{SENTINEL_BASE_URL}/openid/userinfo/",
        client_kwargs={
            'scope': 'openid profile email',
            'token_endpoint_auth_method': 'client_secret_post'
        }
    )
    
    # Build the redirect URI for the callback
    redirect_uri = url_for('callback', _external=True)
    
    # Generate state for security
    state = os.urandom(16).hex()
    session['state'] = state
    
    # Generate nonce for security
    nonce = os.urandom(8).hex()
    session['nonce'] = nonce
    
    # First redirect to the organization-specific login page
    login_url = f"{SENTINEL_BASE_URL}/account/login/"
    
    # Build the authorization URL that will be used after login
    auth_params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': 'openid profile email',
        'state': state,
        'nonce': nonce,
        'organization_id': org_slug  # Add organization context to the authorization request
    }
    
    auth_url = f"{SENTINEL_BASE_URL}/openid/authorize/?{urlencode(auth_params)}"
    
    # Build the login URL with organization context and next parameter
    login_params = {
        'organization': org_slug,
        'next': auth_url
    }
    
    final_url = f"{login_url}?{urlencode(login_params)}"
    
    return redirect(final_url)


@app.route('/callback')
def callback():
    """Handle the OAuth callback"""
    # Verify state for security
    if 'state' in session and request.args.get('state') != session['state']:
        return "State verification failed", 400
    
    sentinel_oauth = oauth.create_client('sentinel')
    
    # Exchange the authorization code for tokens
    token = sentinel_oauth.authorize_access_token()
    
    # Get user info from the userinfo endpoint
    resp = sentinel_oauth.get('userinfo')
    userinfo = resp.json()
    
    # Store user info in session
    session['userinfo'] = userinfo
    
    # Get organization info
    org_slug = session.get('org_slug')
    organization = ORGANIZATIONS.get(org_slug)
    
    return render_template_string(
        CALLBACK_TEMPLATE, 
        userinfo=userinfo,
        organization=organization
    )


@app.route('/logout')
def logout():
    """Handle logout"""
    # Clear session
    session.clear()
    
    # Redirect to home page
    return redirect(url_for('index'))


# Helper function for templates
def render_template_string(template, **context):
    """Render a template string with Flask's template engine"""
    from flask import render_template_string as flask_render_template_string
    return flask_render_template_string(template, **context)


if __name__ == '__main__':
    # Enable HTTPS for secure operation in production
    app.run(debug=True, port=5000) 
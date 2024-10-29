from social_core.backends.oauth import BaseOAuth2
from social_core.backends.google import BaseGoogleOAuth2API

from oidc_provider.models import Organization, OrganizationIdentityProvider

class GoogleOAuth2Backend(BaseGoogleOAuth2API, BaseOAuth2):
    """Google OAuth2 authentication backend"""

    name = "google-oauth2"
    REDIRECT_STATE = False
    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
    ACCESS_TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
    ACCESS_TOKEN_METHOD = "POST"
    REVOKE_TOKEN_URL = "https://accounts.google.com/o/oauth2/revoke"
    REVOKE_TOKEN_METHOD = "GET"
    # The order of the default scope is important
    DEFAULT_SCOPE = ["openid", "email", "profile"]
    EXTRA_DATA = [
        ("refresh_token", "refresh_token", True),
        ("expires_in", "expires"),
        ("token_type", "token_type", True),
    ]

    def __init__(self, strategy, redirect_uri=None, *args, **kwargs):
        response = super().__init__(strategy, redirect_uri)
        # if 'org_slug' in kwargs:
        #     self.org_slug = kwargs['org_slug']
        return response
    
    def get_key_and_secret(self):
        """Return tuple with Consumer Key and Consumer Secret for current
        service provider. Must return (key, secret), order *must* be respected.
        """
        # organization = Organization.objects.get(slug=self.org_slug)
        idp = OrganizationIdentityProvider.objects.last()
        return idp.configuration['client_id'], idp.configuration['client_secret']
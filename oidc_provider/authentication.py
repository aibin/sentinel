# authentication.py

from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from oidc_provider.models import ManagementAccessToken


class SystemUser(AnonymousUser):
    is_staff = True
    is_active = True


class ManagementTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        timestamp = request.headers.get("Timestamp")

        try:
            token_type, signed_token = auth_header.split()
            if token_type.lower() != "bearer":
                return None

            # Verify the token
            management_token = ManagementAccessToken.verify_token(
                signed_token, int(timestamp)
            )
            if management_token:
                return (SystemUser(), management_token)
            else:
                raise AuthenticationFailed("Invalid or expired token")
        except (ValueError, TypeError):
            raise AuthenticationFailed("Invalid token header format")

import time

from django.conf import settings as django_settings
from django.contrib.sessions.backends.base import UpdateError
from django.contrib.sessions.exceptions import SessionInterrupted
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import http_date

from oidc_provider import settings
from oidc_provider.lib.utils.common import get_browser_state_or_default
from oidc_provider.models import Organization


class SessionManagementMiddleware(MiddlewareMixin):
    """
    Maintain a `op_browser_state` cookie along with the `sessionid` cookie that
    represents the End-User's login state at the OP. If the user is not logged
    in then use the value of settings.OIDC_UNAUTHENTICATED_SESSION_MANAGEMENT_KEY.
    """

    def process_response(self, request, response):
        if settings.get("OIDC_SESSION_MANAGEMENT_ENABLE"):
            response.set_cookie(
                "op_browser_state", get_browser_state_or_default(request)
            )
        return response


class SentinelSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        organization_id = request.GET.get("organization_id") or request.POST.get(
            "organization_id"
        )
        try:
            organization = None
            if organization_id:
                organization = Organization.objects.get(id=organization_id)
            else:
                organization = Organization.get_default()
        except Organization.DoesNotExist:
            raise Exception("Organization not found")

        session_key = request.COOKIES.get(
            f"{django_settings.SESSION_COOKIE_NAME}_{organization.id}"
        )
        request.organization = organization
        request.session = self.SessionStore(session_key)
        request.session["organization_id"] = organization.id
        request.session.modified = True

    def process_response(self, request, response):
        """
        If request.session was modified, or if the configuration is to save the
        session every time, save the changes and set a session cookie or delete
        the session cookie if the session has been emptied.
        """
        try:
            accessed = request.session.accessed
            modified = request.session.modified
            empty = request.session.is_empty()
        except AttributeError:
            return response
        # First check if we need to delete this cookie.
        # The session should be deleted only if the session is entirely empty.
        cookie_name = f"{django_settings.SESSION_COOKIE_NAME}_{request.session.get('organization_id')}"
        if cookie_name in request.COOKIES and empty:
            response.delete_cookie(
                cookie_name,
                path=django_settings.SESSION_COOKIE_PATH,
                domain=django_settings.SESSION_COOKIE_DOMAIN,
                samesite=django_settings.SESSION_COOKIE_SAMESITE,
            )
            patch_vary_headers(response, ("Cookie",))
        else:
            if accessed:
                patch_vary_headers(response, ("Cookie",))
            if (modified or django_settings.SESSION_SAVE_EVERY_REQUEST) and not empty:
                if request.session.get_expire_at_browser_close():
                    max_age = None
                    expires = None
                else:
                    max_age = request.session.get_expiry_age()
                    expires_time = time.time() + max_age
                    expires = http_date(expires_time)
                # Save the session data and refresh the client cookie.
                # Skip session save for 5xx responses.
                if response.status_code < 500:
                    try:
                        request.session.save()
                    except UpdateError:
                        raise SessionInterrupted(
                            "The request's session was deleted before the "
                            "request completed. The user may have logged "
                            "out in a concurrent request, for example."
                        )
                    response.set_cookie(
                        cookie_name,
                        request.session.session_key,
                        max_age=max_age,
                        expires=expires,
                        domain=django_settings.SESSION_COOKIE_DOMAIN,
                        path=django_settings.SESSION_COOKIE_PATH,
                        secure=django_settings.SESSION_COOKIE_SECURE or None,
                        httponly=django_settings.SESSION_COOKIE_HTTPONLY or None,
                        samesite=django_settings.SESSION_COOKIE_SAMESITE,
                    )
        return response

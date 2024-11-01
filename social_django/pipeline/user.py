from social_django.backends.google import GoogleOAuth2Backend


def verify_email(strategy, details, backend, user=None, *args, **kwargs):
    if backend.name not in [
        GoogleOAuth2Backend.name,
    ]:
        return
    if not user.email_verified:
        user.email_verified = True
        user.save()

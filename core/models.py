import base64
import hashlib
import secrets

from django.apps import apps
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.encoding import force_bytes, smart_str
from django.utils.translation import gettext_lazy as _
from shortuuid.django_fields import ShortUUIDField


def default_username(email):
    username = base64.urlsafe_b64encode(
        hashlib.sha1(force_bytes(email)).digest()
    ).rstrip(b"=")

    return smart_str(username)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError("The given username must be set")
        email = self.normalize_email(email)
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        username = GlobalUserModel.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        if password:
            user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, *args, **kwargs):
        # If username is not provided, generate a default username
        if not kwargs.get("username"):
            kwargs["username"] = default_username(kwargs.get("email"))
        if "password" not in kwargs:
            kwargs["password"] = None
        kwargs.setdefault("is_staff", False)
        kwargs.setdefault("is_superuser", False)
        return self._create_user(*args, **kwargs)

    def create_superuser(self, *args, **kwargs):
        # If username is not provided, generate a default username
        if not kwargs.get("username"):
            kwargs["username"] = default_username(kwargs.get("email"))
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)

        if kwargs.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if kwargs.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(*args, **kwargs)

    def with_perm(
        self, perm, is_active=True, include_superusers=True, backend=None, obj=None
    ):
        if backend is None:
            backends = auth._get_backends(return_tuples=True)
            if len(backends) == 1:
                backend, _ = backends[0]
            else:
                raise ValueError(
                    "You have multiple authentication backends configured and "
                    "therefore must provide the `backend` argument."
                )
        elif not isinstance(backend, str):
            raise TypeError(
                "backend must be a dotted import path string (got %r)." % backend
            )
        else:
            backend = auth.load_backend(backend)
        if hasattr(backend, "with_perm"):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()


class User(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Username and password are required. Other fields are optional.
    """

    id = ShortUUIDField(unique=True, primary_key=True, length=16)

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), unique=True)
    email_verified = models.BooleanField(_("email verified"), default=False)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = settings.DEFAULT_LOGIN_FIELD
    REQUIRED_FIELDS = ["email"] if settings.DEFAULT_LOGIN_FIELD == "username" else []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = default_username(self.email)
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return self.get_full_name()


class PasswordSetupToken(models.Model):
    PURPOSE_CHOICES = [
        ("setup", "Setup Password"),
        ("reset", "Reset Password"),
    ]
    id = ShortUUIDField(primary_key=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_tokens",
        verbose_name="User",
    )
    token = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    next_url = models.URLField(
        blank=True, null=True, help_text="URL to redirect to after password setup"
    )
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Password Token"
        verbose_name_plural = "Password Tokens"

    def __str__(self):
        return f"Token for {self.user}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)  # Generate a secure random token
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(
                hours=24
            )  # 24-hour expiration by default
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if the token is still valid (i.e., not expired)."""
        return timezone.now() < self.expires_at and not self.used

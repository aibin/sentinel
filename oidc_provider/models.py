import base64
import binascii
import json
from hashlib import md5, sha256

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from shortuuid.django_fields import ShortUUIDField

CLIENT_TYPE_CHOICES = [
    ("confidential", "Confidential"),
    ("public", "Public"),
]

RESPONSE_TYPE_CHOICES = [
    ("code", "code (Authorization Code Flow)"),
    ("id_token", "id_token (Implicit Flow)"),
    ("id_token token", "id_token token (Implicit Flow)"),
    ("code token", "code token (Hybrid Flow)"),
    ("code id_token", "code id_token (Hybrid Flow)"),
    ("code id_token token", "code id_token token (Hybrid Flow)"),
]

JWT_ALGS = [
    ("HS256", "HS256"),
    ("RS256", "RS256"),
]


class ResponseTypeManager(models.Manager):
    def get_by_natural_key(self, value):
        return self.get(value=value)


class ResponseType(models.Model):
    objects = ResponseTypeManager()

    value = models.CharField(
        max_length=30,
        choices=RESPONSE_TYPE_CHOICES,
        unique=True,
        verbose_name=_("Response Type Value"),
    )
    description = models.CharField(
        max_length=50,
    )

    def natural_key(self):
        return (self.value,)  # natural_key must return tuple

    def __str__(self):
        return "{0}".format(self.description)


class Client(models.Model):
    name = models.CharField(max_length=100, default="", verbose_name=_("Name"))
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Owner"),
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        related_name="oidc_clients_set",
    )
    client_type = models.CharField(
        max_length=30,
        choices=CLIENT_TYPE_CHOICES,
        default="confidential",
        verbose_name=_("Client Type"),
        help_text=_(
            "<b>Confidential</b> clients are capable of maintaining the confidentiality"
            " of their credentials. <b>Public</b> clients are incapable."
        ),
    )
    client_id = ShortUUIDField(
        unique=True, verbose_name=_("Client ID"), primary_key=True
    )
    client_secret = models.CharField(
        max_length=255, blank=True, verbose_name=_("Client SECRET")
    )
    response_types = models.ManyToManyField(ResponseType)
    jwt_alg = models.CharField(
        max_length=10,
        choices=JWT_ALGS,
        default="RS256",
        verbose_name=_("JWT Algorithm"),
        help_text=_("Algorithm used to encode ID Tokens."),
    )
    date_created = models.DateField(auto_now_add=True, verbose_name=_("Date Created"))
    website_url = models.CharField(
        max_length=255, blank=True, default="", verbose_name=_("Website URL")
    )
    terms_url = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Terms URL"),
        help_text=_("External reference to the privacy policy of the client."),
    )
    contact_email = models.CharField(
        max_length=255, blank=True, default="", verbose_name=_("Contact Email")
    )
    logo = models.FileField(
        blank=True,
        default="",
        upload_to="oidc_provider/clients",
        verbose_name=_("Logo Image"),
    )
    reuse_consent = models.BooleanField(
        default=True,
        verbose_name=_("Reuse Consent?"),
        help_text=_(
            "If enabled, server will save the user consent given to a specific client, "
            "so that user won't be prompted for the same authorization multiple times."
        ),
    )
    require_consent = models.BooleanField(
        default=True,
        verbose_name=_("Require Consent?"),
        help_text=_("If disabled, the Server will NEVER ask the user for consent."),
    )
    _redirect_uris = models.TextField(
        default="",
        verbose_name=_("Redirect URIs"),
        help_text=_("Enter each URI on a new line."),
    )
    _post_logout_redirect_uris = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Post Logout Redirect URIs"),
        help_text=_("Enter each URI on a new line."),
    )
    _scope = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Scopes"),
        help_text=_("Specifies the authorized scope values for the client app."),
    )

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")

    def __str__(self):
        return "{0}".format(self.name)

    def __unicode__(self):
        return self.__str__()

    def response_type_values(self):
        return (response_type.value for response_type in self.response_types.all())

    def response_type_descriptions(self):
        # return as a list, rather than a generator, so descriptions display correctly in admin
        return [
            response_type.description for response_type in self.response_types.all()
        ]

    @property
    def redirect_uris(self):
        return self._redirect_uris.splitlines()

    @redirect_uris.setter
    def redirect_uris(self, value):
        self._redirect_uris = "\n".join(value)

    @property
    def post_logout_redirect_uris(self):
        return self._post_logout_redirect_uris.splitlines()

    @post_logout_redirect_uris.setter
    def post_logout_redirect_uris(self, value):
        self._post_logout_redirect_uris = "\n".join(value)

    @property
    def scope(self):
        return self._scope.split()

    @scope.setter
    def scope(self, value):
        self._scope = " ".join(value)

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0] if self.redirect_uris else ""


class BaseCodeTokenModel(models.Model):

    client = models.ForeignKey(
        Client, verbose_name=_("Client"), on_delete=models.CASCADE
    )
    organization = models.ForeignKey(
        "Organization",
        verbose_name=_("Organization"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField(verbose_name=_("Expiration Date"))
    _scope = models.TextField(default="", verbose_name=_("Scopes"))

    class Meta:
        abstract = True

    @property
    def scope(self):
        return self._scope.split()

    @scope.setter
    def scope(self, value):
        self._scope = " ".join(value)

    def __unicode__(self):
        return self.__str__()

    def has_expired(self):
        return timezone.now() >= self.expires_at


class Code(BaseCodeTokenModel):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE
    )
    code = models.CharField(max_length=255, unique=True, verbose_name=_("Code"))
    nonce = models.CharField(
        max_length=255, blank=True, default="", verbose_name=_("Nonce")
    )
    is_authentication = models.BooleanField(
        default=False, verbose_name=_("Is Authentication?")
    )
    code_challenge = models.CharField(
        max_length=255, null=True, verbose_name=_("Code Challenge")
    )
    code_challenge_method = models.CharField(
        max_length=255, null=True, verbose_name=_("Code Challenge Method")
    )

    class Meta:
        verbose_name = _("Authorization Code")
        verbose_name_plural = _("Authorization Codes")

    def __str__(self):
        return "{0} - {1}".format(self.client, self.code)


class Token(BaseCodeTokenModel):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        verbose_name=_("User"),
        on_delete=models.CASCADE,
    )
    access_token = models.CharField(
        max_length=255, unique=True, verbose_name=_("Access Token")
    )
    refresh_token = models.CharField(
        max_length=255, unique=True, verbose_name=_("Refresh Token")
    )
    _id_token = models.TextField(verbose_name=_("ID Token"))

    class Meta:
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")

    @property
    def id_token(self):
        return json.loads(self._id_token) if self._id_token else None

    @id_token.setter
    def id_token(self, value):
        self._id_token = json.dumps(value)

    def __str__(self):
        return "{0} - {1}".format(self.client, self.access_token)

    @property
    def at_hash(self):
        # @@@ d-o-p only supports 256 bits (change this if that changes)
        hashed_access_token = (
            sha256(self.access_token.encode("ascii")).hexdigest().encode("ascii")
        )
        return (
            base64.urlsafe_b64encode(
                binascii.unhexlify(hashed_access_token[: len(hashed_access_token) // 2])
            )
            .rstrip(b"=")
            .decode("ascii")
        )


class UserConsent(BaseCodeTokenModel):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE
    )
    date_given = models.DateTimeField(verbose_name=_("Date Given"))

    class Meta:
        unique_together = ("user", "client")


class RSAKey(models.Model):

    key = models.TextField(
        verbose_name=_("Key"), help_text=_("Paste your private RSA Key here.")
    )

    class Meta:
        verbose_name = _("RSA Key")
        verbose_name_plural = _("RSA Keys")

    def __str__(self):
        return "{0}".format(self.kid)

    def __unicode__(self):
        return self.__str__()

    @property
    def kid(self):
        return "{0}".format(
            md5(self.key.encode("utf-8")).hexdigest() if self.key else ""
        )


class Organization(models.Model):
    id = ShortUUIDField(primary_key=True, editable=False)
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    # Logo
    logo = models.FileField(
        blank=True,
        default="",
        upload_to="oidc_provider/organizations",
        verbose_name=_("Logo Image"),
    )

    website_url = models.CharField(
        max_length=255, blank=True, default="", verbose_name=_("Website URL")
    )
    terms_url = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Terms URL"),
        help_text=_("External reference to the privacy policy of the client."),
    )
    contact_email = models.CharField(
        max_length=255, blank=True, default="", verbose_name=_("Contact Email")
    )

    default = models.BooleanField(
        default=False,
        verbose_name=_("Default"),
        help_text=_("Set this connection as default."),
    )

    @classmethod
    def get_default(cls):
        return cls.objects.get(default=True)

    def save(self, *args, **kwargs):
        if self.default:
            # Select all other active connections
            qs = type(self).objects.filter(default=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            # Set default to False
            qs.update(default=False)

        super().save(*args, **kwargs)

    def get_all_users(self):
        User = apps.get_model(settings.AUTH_USER_MODEL)
        if self.default:
            # Get AUTH_USER_MODEL.
            return User.objects.all()
        else:
            # Return user queryset from organization users model
            org_users = OrganizationUser.objects.filter(organization=self).values_list(
                "user", flat=True
            )
            return User.objects.filter(id__in=org_users)

    def get_userroles_for_client(self, user, client):
        connection_grants = []
        user_roles = []
        if self.default:
            connection_grants = Group.objects.all()
            user_roles = user.groups.all()
        else:
            connection = Connection.objects.get(client=client, organization=self)
            connection_grants = connection.grants.all()
            user_connection_roles = OrganizationUser.objects.get(
                organization=self, user=user
            ).roles.all()
            user_roles = user.groups.union(user_connection_roles)

        roles = []
        for role in user_roles:
            if role in connection_grants:
                roles.append(role)
        return roles

    def __str__(self):
        return "{0}".format(self.name)


class Connection(models.Model):
    # Organization
    organization = models.ForeignKey(
        Organization,
        verbose_name=_("Organization"),
        on_delete=models.CASCADE,
        related_name="connections",
    )

    # Client
    client = models.ForeignKey(
        Client,
        verbose_name=_("Client"),
        on_delete=models.CASCADE,
        related_name="connections",
    )

    # Enable or Disable
    active = models.BooleanField(
        default=True,
        verbose_name=_("Enabled"),
        help_text=_("Enable or Disable this connection."),
    )

    # A list of emails domains that are allowed to register
    _email_domains = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Email Domains"),
        help_text=_("Enter each domain on a new line."),
    )

    grants = models.ManyToManyField(Group, verbose_name=_("Grants"))

    enable_mfa = models.BooleanField(
        default=False,
        verbose_name=_("Enable MFA"),
        help_text=_("Enable Multi-Factor Authentication for this connection."),
    )

    # Prevent user auth if at least user role not in grants
    prevent_auth = models.BooleanField(
        default=False,
        verbose_name=_("Prevent Auth"),
        help_text=_("Prevent user authentication if at least user role not in grants."),
    )

    # Include user roles in id_token
    include_roles = models.BooleanField(
        default=False,
        verbose_name=_("Include Roles"),
        help_text=_("Include user roles in id_token."),
    )

    # Allow nrew user registration
    allow_registration = models.BooleanField(
        default=False,
        verbose_name=_("Allow Registration"),
        help_text=_("Allow new user registration."),
    )

    class Meta:
        unique_together = ("client", "organization")

    @property
    def email_domains(self):
        return self._email_domains.splitlines()

    @email_domains.setter
    def email_domains(self, value):
        self._email_domains = "\n".join(value)

    def __str__(self):
        return "{0} - {1}".format(self.client, self.organization)


class OrganizationUser(models.Model):
    id = ShortUUIDField(primary_key=True, editable=False)
    organization = models.ForeignKey(
        Organization,
        verbose_name=_("Organization"),
        on_delete=models.CASCADE,
        related_name="users",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("User"),
        on_delete=models.CASCADE,
        related_name="organizations",
    )
    roles = models.ManyToManyField(Group, verbose_name=_("Roles"), blank=True)

    class Meta:
        unique_together = ("organization", "user")

    def __str__(self):
        return "{0} - {1}".format(self.organization, self.user)

    def __unicode__(self):
        return self.__str__()

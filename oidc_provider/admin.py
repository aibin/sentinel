from hashlib import sha224
from random import randint
from uuid import uuid4

from django.contrib import admin
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from oidc_provider.models import (
    Membership,
    Client,
    Code,
    Connection,
    IdentityProvider,
    ManagementToken,
    Organization,
    RSAKey,
    Token,
    UserConsent,
)


class ClientForm(ModelForm):

    class Meta:
        model = Client
        exclude = []

    def __init__(self, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        self.fields["client_id"].required = False
        self.fields["client_id"].widget.attrs["disabled"] = "true"
        self.fields["client_secret"].required = False
        self.fields["client_secret"].widget.attrs["disabled"] = "true"

    def clean_client_id(self):
        instance = getattr(self, "instance", None)
        if instance and instance.pk:
            return instance.client_id
        else:
            return str(randint(1, 999999)).zfill(6)

    def clean_client_secret(self):
        instance = getattr(self, "instance", None)

        secret = ""

        if instance and instance.pk:
            if (
                self.cleaned_data["client_type"] == "confidential"
            ) and not instance.client_secret:
                secret = sha224(uuid4().hex.encode()).hexdigest()
            elif (
                self.cleaned_data["client_type"] == "confidential"
            ) and instance.client_secret:
                secret = instance.client_secret
        else:
            if self.cleaned_data["client_type"] == "confidential":
                secret = sha224(uuid4().hex.encode()).hexdigest()

        return secret


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):

    fieldsets = [
        [
            _(""),
            {
                "fields": (
                    "name",
                    "owner",
                    "client_type",
                    "response_types",
                    "_redirect_uris",
                    "jwt_alg",
                    "require_consent",
                    "reuse_consent",
                    "allow_registration",
                ),
            },
        ],
        [
            _("Credentials"),
            {
                "fields": ("client_id", "client_secret", "_scope"),
            },
        ],
        [
            _("Information"),
            {
                "fields": (
                    "contact_email",
                    "website_url",
                    "terms_url",
                    "logo",
                    "date_created",
                ),
            },
        ],
        [
            _("Session Management"),
            {
                "fields": ("_post_logout_redirect_uris",),
            },
        ],
    ]
    form = ClientForm
    list_display = ["name", "client_id", "response_type_descriptions", "date_created"]
    readonly_fields = ["date_created"]
    search_fields = ["name"]
    raw_id_fields = ["owner"]


@admin.register(Code)
class CodeAdmin(admin.ModelAdmin):

    raw_id_fields = ["user"]

    def has_add_permission(self, request):
        return False


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):

    raw_id_fields = ["user"]

    def has_add_permission(self, request):
        return False


@admin.register(RSAKey)
class RSAKeyAdmin(admin.ModelAdmin):

    readonly_fields = ["kid"]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "default"]


@admin.register(Membership)
class AssociationAdmin(admin.ModelAdmin):
    pass


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Get the object (Connection instance) if we are editing an existing instance
        obj = self.get_object(request, request.resolver_match.kwargs.get("object_id"))
        if db_field.name == "identity_providers" and obj:
            kwargs["queryset"] = IdentityProvider.objects.filter(
                organization=obj.organization
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    list_display = ["client", "organization", "active"]


@admin.register(UserConsent)
class UserConsentAdmin(admin.ModelAdmin):
    pass


@admin.register(ManagementToken)
class ManagementTokenAdmin(admin.ModelAdmin):
    list_display = ["id", "token", "issued_on", "expires_at", "revoked"]

    def has_add_permission(self, request):
        return False


@admin.register(IdentityProvider)
class IdentityProviderAdmin(admin.ModelAdmin):
    pass

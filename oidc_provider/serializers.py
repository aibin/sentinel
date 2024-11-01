from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import serializers

from core.email.tasks import send_setup_account_email, send_welcome_email
from core.models import PasswordToken
from oidc_provider.models import Association, Organization

User = get_user_model()


class UserCreateSerializer(serializers.Serializer):
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), required=False
    )
    roles = serializers.SlugRelatedField(
        queryset=Group.objects.all(),
        slug_field="name",
        many=True,
        required=False,
        help_text="List of role names (group names) for the user",
    )
    send_email = serializers.BooleanField(default=False, required=False)
    username = serializers.CharField(
        required=(settings.DEFAULT_LOGIN_FIELD == "username")
    )
    email = serializers.EmailField()
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        """Custom email validation to handle existing users gracefully."""
        # Check if a user with this email already exists
        if User.objects.filter(email=value).exists():
            self.existing_user = User.objects.get(email=value)  # Store existing user
        else:
            self.existing_user = None  # Set to None if email does not exist
        return value

    def create(self, validated_data):
        # Extract organization and roles from the validated data
        organization = validated_data.pop("organization_id", Organization.get_default())
        roles = validated_data.pop("roles", [])
        send_email = validated_data.pop("send_email")

        # Use existing user if email already exists, otherwise create a new user
        if self.existing_user:
            user = self.existing_user
            new_user = False
        else:
            user = User(**validated_data)
            user.save()
            new_user = True

        # Check if the user is already part of the organization
        organization_user, created = Association.objects.get_or_create(
            user=user, organization=organization
        )
        if not created:
            raise serializers.ValidationError(
                {
                    "email": "A user with this email is already registered in the organization."
                }
            )

        # Assign roles if this is a new organization-user relationship
        organization_user.roles.set(roles)

        # Send appropriate email if requested
        if send_email:
            next_url = None
            if organization and organization.post_password_update_url:
                next_url = organization.post_password_update_url
            if new_user:
                token = PasswordToken.objects.create(
                    user=user, purpose="setup", next_url=next_url
                )
                url = reverse("core:update_password", args=[token.token])
                url = self.context["request"].build_absolute_uri(url)
                send_setup_account_email.delay(
                    user.full_name,
                    organization.name,
                    user.email,
                    url,
                )
            else:
                send_welcome_email.delay(
                    user.full_name,
                    organization.name,
                    user.email,
                    next_url,
                )

        return organization_user


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for nested user details in the response."""

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]


class AssociationResponseSerializer(serializers.ModelSerializer):
    user = UserDetailSerializer(read_only=True)
    roles = serializers.SlugRelatedField(
        many=True, slug_field="name", queryset=Group.objects.all()
    )

    class Meta:
        model = Association
        fields = ["id", "user", "roles", "organization", "active"]


class UserUpdateSerializer(serializers.Serializer):
    roles = serializers.SlugRelatedField(
        queryset=Group.objects.all(),
        slug_field="name",
        many=True,
        required=False,
        help_text="List of role names (group names) for the user",
    )
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        required=True,
    )
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    active = serializers.BooleanField(required=False)

    def update(self, user, validated_data):
        # Fetch the Association instance
        try:
            instance = Association.objects.get(
                user=user, organization=validated_data["organization_id"]
            )
        except Association.DoesNotExist:
            raise serializers.ValidationError(
                {"organization_id": "User is not part of the organization."}
            )

        # Update user fields if provided
        instance.user.first_name = validated_data.get("first_name", user.first_name)
        instance.user.last_name = validated_data.get("last_name", user.last_name)
        instance.user.save()

        # Update roles if provided
        roles = validated_data.get("roles")
        if roles is not None:
            instance.roles.set(roles)

        # Update active status if provided
        active = validated_data.get("active")
        if active is not None:
            instance.active = active
            instance.save()

        return instance

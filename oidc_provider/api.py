from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from oidc_provider.authentication import ManagementTokenAuthentication
from oidc_provider.serializers import (
    MembershipResponseSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


@api_view(["POST"])
@authentication_classes([ManagementTokenAuthentication])
@permission_classes([IsAdminUser])
def create_user(request):
    serializer = UserCreateSerializer(data=request.data, context={"request": request})
    if serializer.is_valid():
        organization_user = serializer.save()
        # Serialize the Association object
        response_serializer = MembershipResponseSerializer(organization_user)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT", "PATCH"])
@authentication_classes([ManagementTokenAuthentication])
@permission_classes([IsAdminUser])
def update_user(request, user_id):
    try:
        # Fetch the User instance by ID
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    # Update the instance using the provided data
    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        updated_org_user = serializer.save()

        # Serialize the updated Association instance
        response_serializer = MembershipResponseSerializer(updated_org_user)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

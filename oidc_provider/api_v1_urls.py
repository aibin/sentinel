from django.urls import path

from oidc_provider import api

urlpatterns = [
    path("organization/user/", api.create_user, name="create_user"),
    path("organization/user/<str:user_id>/", api.update_user, name="update_user"),
]

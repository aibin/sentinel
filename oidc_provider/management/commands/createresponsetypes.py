# This script is used to populate the response types model with default values
from django.core.management.base import BaseCommand

from oidc_provider.models import ResponseType


class Command(BaseCommand):
    help = "Create the response types model with default values"

    def handle(self, *args, **options):
        RESPONSE_TYPES = [
            ("code", "code (Authorization Code Flow)"),
            ("id_token", "id_token (Implicit Flow)"),
            ("id_token token", "id_token token (Implicit Flow)"),
            ("code token", "code token (Hybrid Flow)"),
            ("code id_token", "code id_token (Hybrid Flow)"),
            ("code id_token token", "code id_token token (Hybrid Flow)"),
        ]
        for value, description in RESPONSE_TYPES:
            ResponseType.objects.create(value=value, description=description)

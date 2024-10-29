# This script is used to populate the response types model with default values
from logging import getLogger

from django.conf import settings
from django.core.management.base import BaseCommand

from oidc_provider.models import ManagementAccessToken

log = getLogger(__name__)


class Command(BaseCommand):
    help = "Create management token."

    def handle(self, *args, **options):
        token = ManagementAccessToken.create_token()

        if token:
            log.debug(f"Token created: f{token.token}")
            self.stdout.write(self.style.SUCCESS(f"Token created: {token.token}"))
        else:
            log.error("Token not created")
            self.stdout.write(self.style.ERROR("Token not created"))

# This script is used to populate the response types model with default values
from logging import getLogger

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

log = getLogger(__name__)


class Command(BaseCommand):
    help = "Create the default organization."

    def handle(self, *args, **options):
        # Create the default groups
        for group in settings.OIDC_OP_DEFAULT_GROUPS:
            Group.objects.get_or_create(name=group)
            log.debug(f'Group "{group}" created')
            self.stdout.write(
                self.style.SUCCESS(f'Group "{group}" created successfully.')
            )

# This script is used to populate the response types model with default values
from logging import getLogger

from django.conf import settings
from django.core.management.base import BaseCommand

from oidc_provider.models import Organization

log = getLogger(__name__)


class Command(BaseCommand):
    help = "Create the default organization."

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            type=str,
            help="Specify the name for the organization. If not provided, the default organization name will be used.",
        )

    def handle(self, *args, **options):
        # Use provided name or fallback to default from settings
        organization_name = options["name"] or settings.DEFAULT_ORG_NAME
        # Create a slug from the organization name, trim, lower case and replace spaces with underscores
        organization_slug = organization_name.strip().lower().replace(" ", "_")

        # get or create organization
        organization, created = Organization.objects.get_or_create(
            slug=organization_slug, defaults={"default": True, "name": organization_name}
        )

        if created:
            log.debug(f'Organization "{organization_name}" created')
            self.stdout.write(
                self.style.SUCCESS(
                    f'Organization "{organization_name}" created successfully.'
                )
            )
        else:
            log.debug(f'Organization "{organization_name}" already exists')
            self.stdout.write(
                self.style.WARNING(
                    f'Organization "{organization_name}" already exists.'
                )
            )

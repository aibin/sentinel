from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sentinel.settings")

# Create the Celery application instance
app = Celery("sentinel")

# Load the settings for Celery from the Django settings module
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks in your Django apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

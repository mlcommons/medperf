import os

from django.contrib.auth.models import User
from django.db import migrations
from django.db.backends.postgresql.schema import DatabaseSchemaEditor
from django.db.migrations.state import StateApps
from django.conf import settings

import google.auth
from google.cloud import secretmanager


def createsuperuser(apps: StateApps, schema_editor: DatabaseSchemaEditor) -> None:
    """
    Dynamically create an admin user as part of a migration
    """
    
    User.objects.create_superuser(settings.ADMIN_USERNAME, password=settings.ADMIN_PASSWORD)


class Migration(migrations.Migration):

    initial = True
    dependencies = []
    operations = [migrations.RunPython(createsuperuser)]

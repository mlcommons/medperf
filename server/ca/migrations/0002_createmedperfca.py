from django.contrib.auth import get_user_model
from django.db import migrations
from django.db.backends.postgresql.schema import DatabaseSchemaEditor
from django.db.migrations.state import StateApps
from django.conf import settings
from ca.models import CA

User = get_user_model()


def createmedperfca(apps: StateApps, schema_editor: DatabaseSchemaEditor) -> None:
    """
    Dynamically create the configured main CA as part of a migration
    """
    admin_user = User.objects.get(username=settings.SUPERUSER_USERNAME)
    CA.objects.create(
        name=settings.CA_NAME,
        address=settings.CA_ADDRESS,
        port=settings.CA_PORT,
        fingerprint=settings.CA_FINGERPRINT,
        owner=admin_user,
    )


class Migration(migrations.Migration):

    initial = True
    dependencies = [("ca", "0001_initial"), ("user", "0001_createsuperuser")]
    operations = [migrations.RunPython(createmedperfca)]

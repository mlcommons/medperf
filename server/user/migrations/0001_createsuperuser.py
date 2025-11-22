from django.contrib.auth import get_user_model
from django.db import migrations
from django.db.backends.postgresql.schema import DatabaseSchemaEditor
from django.db.migrations.state import StateApps
from django.conf import settings

User = get_user_model()


def createsuperuser(apps: StateApps, schema_editor: DatabaseSchemaEditor) -> None:
    """
    Dynamically create an admin user as part of a migration
    """
    # NOTE: if we later use another user model (e.g., a custom one), this may be problematic.
    User.objects.create_superuser(
        settings.SUPERUSER_USERNAME, password=settings.SUPERUSER_PASSWORD
    )


class Migration(migrations.Migration):

    initial = True
    dependencies = []
    operations = [migrations.RunPython(createsuperuser)]

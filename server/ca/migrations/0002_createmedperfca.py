from django.contrib.auth import get_user_model
from django.db import migrations
from django.db.backends.postgresql.schema import DatabaseSchemaEditor
from django.db.migrations.state import StateApps
from django.conf import settings
from ca.models import CA
from mlcube.models import MlCube

User = get_user_model()


def createmedperfca(apps: StateApps, schema_editor: DatabaseSchemaEditor) -> None:
    """
    Dynamically create the configured main CA as part of a migration
    """
    admin_user = User.objects.get(username=settings.SUPERUSER_USERNAME)
    ca_mlcube = MlCube.objects.create(
        name=settings.CA_MLCUBE_NAME,
        git_mlcube_url=settings.CA_MLCUBE_URL,
        mlcube_hash=settings.CA_MLCUBE_HASH,
        image_hash=settings.CA_MLCUBE_IMAGE_HASH,
        metadata=settings.CA_MLCUBE_METADATA,
        owner=admin_user,
        state="OPERATION",
    )
    CA.objects.create(
        name=settings.CA_NAME,
        config=settings.CA_CONFIG,
        ca_mlcube=ca_mlcube,
        client_mlcube=ca_mlcube,
        server_mlcube=ca_mlcube,
        owner=admin_user,
    )


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("ca", "0001_initial"),
        ("user", "0001_createsuperuser"),
        ("mlcube", "0002_alter_mlcube_unique_together"),
    ]
    operations = [migrations.RunPython(createmedperfca)]

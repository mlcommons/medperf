from django.db import migrations
from django.db.backends.postgresql.schema import DatabaseSchemaEditor
from django.db.migrations.state import StateApps
from django.conf import settings


def createmedperfca(apps: StateApps, schema_editor: DatabaseSchemaEditor) -> None:
    """
    Dynamically create the configured main CA as part of a migration
    """
    # NOTE: if we later use another user model (e.g., a custom one), this may be problematic.
    User = apps.get_model("auth", "User")
    MlCube = apps.get_model("mlcube", "MlCube")
    CA = apps.get_model("ca", "CA")
    admin_user = User.objects.get(username=settings.SUPERUSER_USERNAME)
    ca_mlcube = MlCube.objects.create(
        name=settings.CA_MLCUBE_NAME,
        container_config=settings.CA_CONTAINER_CONFIG,
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
        ("mlcube", "0003_alter_mlcube_unique_together_mlcube_container_config_and_more"),
    ]
    operations = [migrations.RunPython(createmedperfca)]

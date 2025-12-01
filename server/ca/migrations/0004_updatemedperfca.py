from django.db import migrations
from django.db.backends.postgresql.schema import DatabaseSchemaEditor
from django.db.migrations.state import StateApps
from django.conf import settings


def updatemedperfca(apps: StateApps, schema_editor: DatabaseSchemaEditor) -> None:
    """
    Update the CA MLCube config
    """
    MlCube = apps.get_model("mlcube", "MlCube")

    # Update the CA MLCube image hash and metadata (config)
    ca_mlcube = MlCube.objects.get(name=settings.CA_MLCUBE_NAME)
    ca_mlcube.container_config = settings.CA_MLCUBE_CONFIG
    ca_mlcube.save()


class Migration(migrations.Migration):
    dependencies = [
        ("ca", "0003_alter_ca_name"),
        (
            "mlcube",
            "0004_alter_mlcube_unique_together_mlcube_container_config_and_more",
        ),
    ]
    operations = [migrations.RunPython(updatemedperfca)]

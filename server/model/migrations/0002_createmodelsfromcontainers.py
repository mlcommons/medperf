from django.db import migrations
from django.db.backends.postgresql.schema import DatabaseSchemaEditor
from django.db.migrations.state import StateApps


def createmodelsfromcontainers(
    apps: StateApps, schema_editor: DatabaseSchemaEditor
) -> None:

    User = apps.get_model("auth", "User")
    Benchmark = apps.get_model("benchmark", "Benchmark")
    BenchmarkModel = apps.get_model("benchmarkmodel", "BenchmarkModel")
    ModelResult = apps.get_model("result", "ModelResult")
    Model = apps.get_model("model", "Model")
    MlCube = apps.get_model("mlcube", "MlCube")

    model_container_ids = set()
    model_container_ids.update(
        Benchmark.objects.exclude(cube__isnull=True)
        .values_list("reference_model_mlcube", flat=True)
        .distinct()
    )
    model_container_ids.update(
        BenchmarkModel.objects.exclude(cube__isnull=True)
        .values_list("model_mlcube", flat=True)
        .distinct()
    )
    model_container_ids.update(
        ModelResult.objects.exclude(cube__isnull=True)
        .values_list("model", flat=True)
        .distinct()
    )
    container_to_model = {}
    for container_id in model_container_ids:
        container = MlCube.objects.get(id=container_id)
        owner = User.objects.get(id=container.owner_id)
        model_obj = Model.objects.create(
            name=f"Model for container {container.name}",
            container=container,
            owner=owner,
            type="CONTAINER",
            state=container.state,
            is_valid=container.is_valid,
        )
        container_to_model[container_id] = model_obj

    for benchmark in Benchmark.objects.exclude(reference_model_mlcube__isnull=True):
        benchmark.reference_model = container_to_model[benchmark.reference_model_mlcube]
        benchmark.save()

    for benchmark_model in BenchmarkModel.objects.exclude(model_mlcube__isnull=True):
        benchmark_model.model = container_to_model[benchmark_model.model_mlcube]
        benchmark_model.save()

    for model_result in ModelResult.objects.exclude(model__isnull=True):
        model_result.the_model = container_to_model[model_result.model]
        model_result.save()


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("model", "0001_initial"),
        ("benchmark", "0006_benchmark_reference_model"),
        ("benchmarkmodel", "0002_benchmarkmodel_model"),
        ("result", "0006_modelresult_the_model"),
    ]
    operations = [migrations.RunPython(createmodelsfromcontainers)]

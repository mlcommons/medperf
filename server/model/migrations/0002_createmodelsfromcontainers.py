from django.db import migrations
from django.db.backends.postgresql.schema import DatabaseSchemaEditor
from django.db.migrations.state import StateApps


def createmodelsfromcontainers(
    apps: StateApps, schema_editor: DatabaseSchemaEditor
) -> None:

    Benchmark = apps.get_model("benchmark", "Benchmark")
    BenchmarkModel = apps.get_model("benchmarkmodel", "BenchmarkModel")
    ModelResult = apps.get_model("result", "ModelResult")
    Model = apps.get_model("model", "Model")
    MlCube = apps.get_model("mlcube", "MlCube")

    model_container_ids = set()
    model_container_ids.update(
        Benchmark.objects.all()
        .values_list("reference_model_mlcube", flat=True)
        .distinct()
    )
    model_container_ids.update(
        BenchmarkModel.objects.all().values_list("model_mlcube", flat=True).distinct()
    )
    model_container_ids.update(
        ModelResult.objects.all().values_list("model", flat=True).distinct()
    )
    container_to_model = {}
    for container_id in model_container_ids:
        container = MlCube.objects.get(id=container_id)
        model_obj = Model.objects.create(
            name=container.name,
            container=container,
            owner=container.owner,
            type="CONTAINER",
            state=container.state,
            is_valid=container.is_valid,
        )
        container_to_model[container_id] = model_obj

    for benchmark in Benchmark.objects.all():
        benchmark.reference_model = container_to_model[
            benchmark.reference_model_mlcube.id
        ]
        benchmark.save()

    for benchmark_model in BenchmarkModel.objects.all():
        benchmark_model.model = container_to_model[benchmark_model.model_mlcube.id]
        benchmark_model.save()

    for model_result in ModelResult.objects.all():
        model_result.the_model = container_to_model[model_result.model.id]
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

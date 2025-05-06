from rest_framework import serializers
from benchmarkdataset.models import BenchmarkDataset
from benchmarkmodel.models import BenchmarkModel

from .models import ModelResult


class ModelResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelResult
        fields = "__all__"
        read_only_fields = ["owner", "approved_at", "approval_status"]

    def validate(self, data):
        benchmark = data["benchmark"]
        mlcube = data["model"]
        dataset = data["dataset"]
        is_reference_model = benchmark.reference_model_mlcube.id == mlcube.id
        last_benchmarkmodel = (
            BenchmarkModel.objects.filter(
                benchmark__id=benchmark.id, model_mlcube__id=mlcube.id
            )
            .order_by("-created_at")
            .first()
        )
        if not is_reference_model:
            if not last_benchmarkmodel:
                raise serializers.ValidationError(
                    "Model must be associated to the benchmark"
                )
            else:
                if last_benchmarkmodel.approval_status != "APPROVED":
                    raise serializers.ValidationError(
                        "Model-Benchmark association must be approved"
                    )

        last_benchmarkdataset = (
            BenchmarkDataset.objects.filter(
                benchmark__id=benchmark.id, dataset__id=dataset.id
            )
            .order_by("-created_at")
            .first()
        )
        if not last_benchmarkdataset:
            raise serializers.ValidationError(
                "Dataset must be associated to the benchmark"
            )
        else:
            if last_benchmarkdataset.approval_status != "APPROVED":
                raise serializers.ValidationError(
                    "Dataset-Benchmark association must be approved"
                )
        return data


class ModelResultDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelResult
        fields = "__all__"
        read_only_fields = [
            "owner",
            "approved_at",
            "benchmark",
            "model",
            "dataset",
            "results",
        ]

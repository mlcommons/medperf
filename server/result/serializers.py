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
        if benchmark.approval_status != "APPROVED":
            raise serializers.ValidationError("Benchmark must be approved by admin")
        if benchmark.state != "OPERATION":
            raise serializers.ValidationError("Benchmark state must be in operation")
        if model.state != "OPERATION":
            raise serializers.ValidationError("MlCube state must be in operation")
        if dataset.state != "OPERATION":
            raise serializers.ValidationError("Dataset state must be in operation")
        last_benchmarkmodel = (
            BenchmarkModel.objects.filter(benchmark__id=benchmark.id, model_mlcube__id=mlcube.id)
            .order_by("-created_at")
            .first()
        )
        if not last_benchmarkmodel:
            raise serializers.ValidationError("Mlcube must be associated to the benchmark")
        else:
            if last_benchmarkmodel.approval_status != "APPROVED":
                raise serializers.ValidationError("Mlcube-Benchmark association must be approved")
        last_benchmarkdataset = (
            BenchmarkDataset.objects.filter(benchmark__id=benchmark.id, dataset__id=dataset.id).order_by("-created_at").first()
        )
        if not last_benchmarkdataset:
            raise serializers.ValidationError("Dataset must be associated to the benchmark")
        else:
            if last_benchmarkdataset.approval_status != "APPROVED":
                raise serializers.ValidationError("Dataset-Benchmark association must be approved")
        return data

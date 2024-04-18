from rest_framework import serializers
from django.utils import timezone
from benchmark.models import Benchmark
from mlcube.models import MlCube

from .models import BenchmarkModel
from utils.associations import (
    validate_approval_status_on_creation,
    validate_approval_status_on_update,
)


class BenchmarkModelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkModel
        read_only_fields = ["initiated_by", "approved_at", "priority"]
        fields = "__all__"

    def validate(self, data):
        bid = self.context["request"].data.get("benchmark")
        mlcube = self.context["request"].data.get("model_mlcube")
        approval_status = self.context["request"].data.get("approval_status", "PENDING")

        # benchmark state
        benchmark = Benchmark.objects.get(pk=bid)
        benchmark_state = benchmark.state
        if benchmark_state != "OPERATION":
            raise serializers.ValidationError(
                "Association requests can be made only on an operational benchmark"
            )

        # benchmark approval status
        benchmark_approval_status = benchmark.approval_status
        if benchmark_approval_status != "APPROVED":
            raise serializers.ValidationError(
                "Association requests can be made only on an approved benchmark"
            )

        # mlcube state
        mlcube_obj = MlCube.objects.get(pk=mlcube)
        mlcube_state = mlcube_obj.state
        if mlcube_state != "OPERATION":
            raise serializers.ValidationError(
                "Association requests can be made only on an operational model mlcube"
            )

        # approval status
        last_benchmarkmodel = (
            BenchmarkModel.objects.filter(benchmark__id=bid, model_mlcube__id=mlcube)
            .order_by("-created_at")
            .first()
        )
        validate_approval_status_on_creation(last_benchmarkmodel, approval_status)

        return data

    def create(self, validated_data):
        approval_status = validated_data.get("approval_status", "PENDING")
        if approval_status != "PENDING":
            validated_data["approved_at"] = timezone.now()
        else:
            same_owner = (
                validated_data["model_mlcube"].owner.id
                == validated_data["benchmark"].owner.id
            )
            if same_owner:
                validated_data["approval_status"] = "APPROVED"
                validated_data["approved_at"] = timezone.now()
        return BenchmarkModel.objects.create(**validated_data)


class ModelApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkModel
        read_only_fields = ["initiated_by", "approved_at"]
        fields = [
            "approval_status",
            "initiated_by",
            "approved_at",
            "created_at",
            "modified_at",
            "priority",
        ]

    def validate(self, data):
        if not self.instance:
            raise serializers.ValidationError("No model association found")
        return data

    def validate_approval_status(self, cur_approval_status):
        last_approval_status = self.instance.approval_status
        initiated_user = self.instance.initiated_by
        current_user = self.context["request"].user
        validate_approval_status_on_update(
            last_approval_status, cur_approval_status, initiated_user, current_user
        )
        return cur_approval_status

    def update(self, instance, validated_data):
        if "approval_status" in validated_data:
            if validated_data["approval_status"] != instance.approval_status:
                instance.approval_status = validated_data["approval_status"]
                if instance.approval_status != "PENDING":
                    instance.approved_at = timezone.now()
        if "priority" in validated_data:
            instance.priority = validated_data["priority"]
        instance.save()
        return instance


class BenchmarkListofModelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkModel
        fields = ["model_mlcube", "approval_status", "created_at"]

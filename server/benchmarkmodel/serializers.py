from rest_framework import serializers
from django.utils import timezone
from benchmark.models import Benchmark
from mlcube.models import MlCube

from .models import BenchmarkModel


class BenchmarkModelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkModel
        read_only_fields = ["initiated_by", "approved_at"]
        fields = "__all__"

    def validate(self, data):
        bid = self.context["request"].data.get("benchmark")
        mlcube = self.context["request"].data.get("model_mlcube")
        approval_status = self.context["request"].data.get("approval_status", "PENDING")
        benchmark = Benchmark.objects.get(pk=bid)
        benchmark_state = benchmark.state
        if benchmark_state != "OPERATION":
            raise serializers.ValidationError(
                "Association requests can be made only on an operational benchmark"
            )
        benchmark_approval_status = benchmark.approval_status
        if benchmark_approval_status != "APPROVED":
            raise serializers.ValidationError(
                "Association requests can be made only on an approved benchmark"
            )
        mlcube_state = MlCube.objects.get(pk=mlcube).state
        if mlcube_state != "OPERATION":
            raise serializers.ValidationError(
                "Association requests can be made only on an operational model mlcube"
            )
        last_benchmarkmodel = (
            BenchmarkModel.objects.filter(benchmark__id=bid, model_mlcube__id=mlcube)
            .order_by("-created_at")
            .first()
        )
        if not last_benchmarkmodel:
            if approval_status != "PENDING":
                raise serializers.ValidationError(
                    "User can approve or reject association request only if there are prior requests"
                )
        else:
            if approval_status == "PENDING":
                if last_benchmarkmodel.approval_status != "REJECTED":
                    raise serializers.ValidationError(
                        "User can create a new request only if prior request is rejected"
                    )
                # check valid results passed
            elif approval_status == "APPROVED":
                raise serializers.ValidationError(
                    "User cannot create an approved association request"
                )
            # approval_status == "REJECTED":
            else:
                if last_benchmarkmodel.approval_status != "APPROVED":
                    raise serializers.ValidationError(
                        "User can reject request only if prior request is approved"
                    )
        return data

    def create(self, validated_data):
        approval_status = validated_data.get("approval_status", "PENDING")
        if approval_status != "PENDING":
            validated_data["approved_at"] = timezone.now()
        else:
            if (
                validated_data["model_mlcube"].owner.id
                == validated_data["benchmark"].owner.id
            ):
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
        ]

    def validate(self, data):
        if not self.instance:
            raise serializers.ValidationError("No model association found")
        last_approval_status = self.instance.approval_status
        cur_approval_status = data["approval_status"]
        if last_approval_status != "PENDING":
            raise serializers.ValidationError(
                "User can approve or reject only a pending request"
            )
        initiated_user = self.instance.initiated_by
        current_user = self.context["request"].user
        if (
            last_approval_status != cur_approval_status
            and cur_approval_status == "APPROVED"
        ):
            if current_user.id == initiated_user.id:
                raise serializers.ValidationError(
                    "Same user cannot approve the association request"
                )
        return data

    def update(self, instance, validated_data):
        instance.approval_status = validated_data["approval_status"]
        if instance.approval_status != "PENDING":
            instance.approved_at = timezone.now()
        instance.save()
        return instance

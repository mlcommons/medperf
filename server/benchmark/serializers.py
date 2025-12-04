from rest_framework import serializers
from django.utils import timezone
from django.conf import settings
from .models import Benchmark


class BenchmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benchmark
        fields = "__all__"
        read_only_fields = ["owner", "approved_at", "approval_status"]

    def validate(self, data):
        owner = self.context["request"].user
        pending_benchmarks = Benchmark.objects.filter(
            owner=owner, approval_status="PENDING"
        )
        if len(pending_benchmarks) > 0:
            raise serializers.ValidationError(
                "User can own at most one pending benchmark"
            )

        if "state" in data and data["state"] == "OPERATION":
            dev_mlcubes = [
                data["data_preparation_mlcube"].state == "DEVELOPMENT",
                data["reference_model_mlcube"].state == "DEVELOPMENT",
                data["data_evaluator_mlcube"].state == "DEVELOPMENT",
            ]
            if any(dev_mlcubes):
                raise serializers.ValidationError(
                    "User cannot mark a benchmark as operational"
                    " if its containers are not operational"
                )
        if owner.email in settings.AUTO_APPROVE_BENCHMARKS_FROM:
            data["approval_status"] = "APPROVED"
        return data


class BenchmarkApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benchmark
        read_only_fields = ["owner", "approved_at"]
        fields = "__all__"

    def update(self, instance, validated_data):
        if "approval_status" in validated_data:
            if validated_data["approval_status"] != instance.approval_status:
                instance.approval_status = validated_data["approval_status"]
                if instance.approval_status != "PENDING":
                    instance.approved_at = timezone.now()
        validated_data.pop("approval_status", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance

    def validate_approval_status(self, approval_status):
        if approval_status == "PENDING":
            raise serializers.ValidationError(
                "User can only approve or reject a benchmark"
            )
        if approval_status == "APPROVED":
            if self.instance.approval_status == "REJECTED":
                raise serializers.ValidationError(
                    "User can approve only a pending request"
                )
        return approval_status

    def validate_state(self, state):
        if state == "OPERATION" and self.instance.state != "OPERATION":
            dev_mlcubes = [
                self.instance.data_preparation_mlcube.state == "DEVELOPMENT",
                self.instance.reference_model_mlcube.state == "DEVELOPMENT",
                self.instance.data_evaluator_mlcube.state == "DEVELOPMENT",
            ]
            if any(dev_mlcubes):
                raise serializers.ValidationError(
                    "User cannot mark a benchmark as operational"
                    " if its containers are not operational"
                )
        return state

    def validate(self, data):
        if self.instance.state == "OPERATION":
            editable_fields = [
                "is_valid",
                "is_active",
                "user_metadata",
                "approval_status",
                "demo_dataset_tarball_url",
                "dataset_auto_approval_allow_list",
                "dataset_auto_approval_mode",
                "model_auto_approval_allow_list",
                "model_auto_approval_mode",
            ]
            for k, v in data.items():
                if k not in editable_fields:
                    if v != getattr(self.instance, k):
                        raise serializers.ValidationError(
                            "User cannot update non editable fields in Operation mode"
                        )
        return data


class BenchmarkPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benchmark
        exclude = ["dataset_auto_approval_allow_list", "model_auto_approval_allow_list"]

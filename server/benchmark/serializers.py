from rest_framework import serializers
from django.utils import timezone
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
        return data


class BenchmarkApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benchmark
        read_only_fields = ["owner", "approved_at"]
        fields = "__all__"

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)
        # TODO: the condition below will run even
        #       if a user edits the benchmark after it gets approved
        if instance.approval_status != "PENDING":
            instance.approved_at = timezone.now()
        instance.save()
        return instance

    def validate(self, data):
        # TODO: remove the ability to update to PENDING (it just adds complexity?)
        # TODO: define what should happen to existing assets when a benchmark
        #       is rejected after being approved (associations? results? note also
        #       that results submission doesn't check benchmark's approval status)
        owner = self.instance.owner
        if "approval_status" in data:
            if (
                data["approval_status"] == "PENDING"
                and self.instance.approval_status != "PENDING"
            ):
                pending_benchmarks = Benchmark.objects.filter(
                    owner=owner, approval_status="PENDING"
                )
                if len(pending_benchmarks) > 0:
                    raise serializers.ValidationError(
                        "User can own at most one pending benchmark"
                    )
            if (
                data["approval_status"] != "PENDING"
                and self.instance.state == "DEVELOPMENT"
            ):
                raise serializers.ValidationError(
                    "User cannot approve or reject when benchmark is in development stage"
                )
        if self.instance.state == "OPERATION":
            editable_fields = [
                "is_valid",
                "is_active",
                "user_metadata",
                "approval_status",
                "demo_dataset_tarball_url",
            ]
            for k, v in data.items():
                if k not in editable_fields:
                    if v != getattr(self.instance, k):
                        raise serializers.ValidationError(
                            "User cannot update non editable fields in Operation mode"
                        )
        return data

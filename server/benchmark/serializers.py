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
        read_only_fields = ["approved_at"]
        fields = [
            "approval_status",
            "approved_at",
            "created_at",
            "modified_at",
        ]

    def update(self, instance, validated_data):
        instance.approval_status = validated_data["approval_status"]
        if instance.approval_status == "APPROVED":
            instance.approved_at = timezone.now()
        instance.save()
        return instance

    def validate(self, data):
        owner = self.instance.owner
        if data["approval_status"] == "PENDING":
            pending_benchmarks = Benchmark.objects.filter(
                owner=owner, approval_status="PENDING"
            )
            if len(pending_benchmarks) > 0:
                raise serializers.ValidationError(
                    "User can own at most one pending benchmark"
                )
        return data

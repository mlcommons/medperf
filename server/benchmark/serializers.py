from rest_framework import serializers
from django.utils import timezone
from .models import Benchmark


class BenchmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benchmark
        fields = "__all__"
        read_only_fields = ["owner", "approved_at", "approval_status"]


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

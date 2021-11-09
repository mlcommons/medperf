from rest_framework import serializers
from django.utils import timezone
from .models import BenchmarkModel


class BenchmarkModelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkModel
        read_only_fields = ["initiated_by", "approved_at", "approval_status"]
        fields = [
            "model_mlcube",
            "benchmark",
            "initiated_by",
            "approval_status",
            "approved_at",
            "created_at",
            "modified_at",
        ]


class BenchmarkModelApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkModel
        read_only_fields = ["initiated_by", "approved_at", "approval_status"]
        fields = [
            "benchmark",
            "approval_status",
            "initiated_by",
            "approved_at",
            "created_at",
            "modified_at",
        ]


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

    def update(self, instance, validated_data):
        instance.approval_status = validated_data["approval_status"]
        if instance.approval_status == "APPROVED":
            instance.approved_at = timezone.now()
        instance.save()
        return instance

from rest_framework import serializers
from django.utils import timezone
from .models import BenchmarkDataset


class BenchmarkDatasetListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkDataset
        read_only_fields = ["initiated_by", "approved_at", "approval_status"]
        fields = "__all__"


class DatasetApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkDataset
        read_only_fields = ["initiated_by", "approved_at"]
        fields = [
            "approval_status",
            "initiated_by",
            "approved_at",
            "created_at",
            "modified_at",
        ]

    def validate(self, data):
        initiated_user = self.instance.initiated_by
        current_user = self.context["request"].user
        if (
            self.instance.approval_status != data["approval_status"]
            and data["approval_status"] == "APPROVED"
        ):
            if current_user.id == initiated_user.id:
                raise serializers.ValidationError(
                    "Same user cannot approve the association request"
                )
        return data

    def update(self, instance, validated_data):
        instance.approval_status = validated_data["approval_status"]
        if instance.approval_status == "APPROVED":
            instance.approved_at = timezone.now()
        instance.save()
        return instance

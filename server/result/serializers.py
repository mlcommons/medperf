from rest_framework import serializers
from .models import ModelResult


class ModelResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelResult
        fields = "__all__"
        read_only_fields = ["owner", "approved_at", "approval_status"]

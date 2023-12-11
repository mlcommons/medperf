from rest_framework import serializers
from .models import Dataset


class DatasetFullSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = "__all__"
        read_only_fields = ["owner"]


class DatasetPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        exclude = ["owner", "report"]


class DatasetDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        if self.instance.state == "OPERATION":
            editable_fields = ["is_valid", "user_metadata"]
            for k, v in data.items():
                if k not in editable_fields:
                    if v != getattr(self.instance, k):
                        raise serializers.ValidationError(
                            "User cannot update non editable fields in Operation mode"
                        )
        return data

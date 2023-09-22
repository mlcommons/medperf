from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"
        read_only_fields = ["owner"]


class ReportDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        editable_fields = ["is_valid", "user_metadata", "metadata", "contents"]
        for k, v in data.items():
            if k not in editable_fields:
                if v != getattr(self.instance, k):
                    raise serializers.ValidationError(
                        "User cannot update non editable fields"
                    )
        return data

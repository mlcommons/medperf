from rest_framework import serializers
from .models import MlCube


class MlCubeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MlCube
        fields = "__all__"
        read_only_fields = ["owner"]


class MlCubeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MlCube
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        if self.instance.state == "OPERATION":
            editable_fields = [
                "is_valid",
                "user_metadata",
                "image_tarball_url",
                "additional_files_tarball_url",
                "git_mlcube_url",
                "git_parameters_url",
            ]
            for k, v in data.items():
                if k not in editable_fields:
                    if v != getattr(self.instance, k):
                        raise serializers.ValidationError(
                            "User cannot update non editable fields in Operation mode"
                        )
        return data

from rest_framework import serializers
from .models import MlCube


class MlCubeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MlCube
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        git_parameters_url = data["git_parameters_url"]
        parameters_hash = data["parameters_hash"]

        additional_files_tarball_url = data["additional_files_tarball_url"]
        additional_files_tarball_hash = data["additional_files_tarball_hash"]

        image_hash = data["image_hash"]

        image_tarball_url = data["image_tarball_url"]
        image_tarball_hash = data["image_tarball_hash"]

        # validate nonblank parameters file hash
        if git_parameters_url and not parameters_hash:
            raise serializers.ValidationError("Parameters require file hash")

        # validate nonblank additional files hash
        if additional_files_tarball_url and not additional_files_tarball_hash:
            raise serializers.ValidationError("Additional files require file hash")

        # validate images attributes.
        if not image_hash and not image_tarball_hash:
            raise serializers.ValidationError(
                "Image hash or Image tarball hash must be provided"
            )
        if image_hash and image_tarball_hash:
            raise serializers.ValidationError(
                "Image hash and Image tarball hash can't be provided at the same time"
            )
        if image_tarball_url and not image_tarball_hash:
            raise serializers.ValidationError(
                "Providing Image tarball requires providing image tarball hash"
            )

        if not image_tarball_url and image_tarball_hash:
            raise serializers.ValidationError(
                "image tarball hash should not be provided if no image tarball url is provided"
            )

        return data


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

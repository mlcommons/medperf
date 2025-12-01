from rest_framework import serializers
from .models import MlCube


def validate_optional_mlcube_components(data):
    additional_files_tarball_url = data.get("additional_files_tarball_url", "")
    additional_files_tarball_hash = data.get("additional_files_tarball_hash", "")

    image_hash = data.get("image_hash", "")

    image_tarball_url = data.get("image_tarball_url", "")
    image_tarball_hash = data.get("image_tarball_hash", "")

    # validate nonblank additional files hash
    if additional_files_tarball_url and not additional_files_tarball_hash:
        raise serializers.ValidationError("Additional files require file hash")

    if not additional_files_tarball_url and additional_files_tarball_hash:
        raise serializers.ValidationError(
            "Additional files hash was provided without URL"
        )

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


class MlCubeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MlCube
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        validate_optional_mlcube_components(data)
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
            ]
            for k, v in data.items():
                if k not in editable_fields:
                    if v != getattr(self.instance, k):
                        raise serializers.ValidationError(
                            "User cannot update non editable fields in Operation mode"
                        )

        updated_dict = {}
        for key in [
            "container_config",
            "parameters_config",
            "additional_files_tarball_url",
            "additional_files_tarball_hash",
            "image_hash",
            "image_tarball_url",
            "image_tarball_hash",
        ]:
            updated_dict[key] = data.get(key, getattr(self.instance, key))

        validate_optional_mlcube_components(updated_dict)

        return data

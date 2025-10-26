from rest_framework import serializers
from .models import MlCubeKey


class EncryptedKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = MlCubeKey
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        certificate = data["certificate"]
        if not certificate.is_valid:
            raise serializers.ValidationError(
                "Container keys should only be created for valid certificates"
            )
        return data


class EncryptedKeyDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MlCubeKey
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        keys = list(data.keys())
        # Only `is_valid` is allowed to be edited
        if len(keys) != 1 or keys[0] != "is_valid":
            raise serializers.ValidationError(
                "User can only invalidate a container key"
            )
        # `is_valid` is only allowed to become False
        if data["is_valid"]:
            raise serializers.ValidationError(
                "User can only invalidate a container key"
            )
        return data

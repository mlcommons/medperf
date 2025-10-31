from rest_framework import serializers
from .models import Certificate
from user.serializers import UserSerializer


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = "__all__"
        read_only_fields = ["owner"]


class CertificateWithOwnerInfoSerializer(serializers.ModelSerializer):
    """This is needed when getting certificates and their owners
    with one API call."""

    owner = UserSerializer()

    class Meta:
        model = Certificate
        fields = "__all__"


class CertificateDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        keys = list(data.keys())
        # Only `is_valid` is allowed to be edited
        if len(keys) != 1 or keys[0] != "is_valid":
            raise serializers.ValidationError("User can only invalidate a certificate")
        # `is_valid` is only allowed to become False
        if data["is_valid"]:
            raise serializers.ValidationError("User can only invalidate a certificate")
        return data

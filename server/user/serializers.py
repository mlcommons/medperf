from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserExtension

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    metadata = serializers.JSONField(required=False, allow_null=True, default=None)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "metadata",
        )
        read_only_fields = ("id", "username", "email", "first_name", "last_name")

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        try:
            extension = instance.userextension
            representation["metadata"] = extension.metadata
        except UserExtension.DoesNotExist:
            representation["metadata"] = {}
        return representation

    def update(self, instance, validated_data):
        metadata = validated_data.pop("metadata", None)

        instance = super().update(instance, validated_data)

        # Update or create UserExtension
        if metadata is not None:
            extension, _ = UserExtension.objects.get_or_create(user=instance)
            extension.metadata = metadata
            extension.save()

        return instance


class UserMetadataSerializer(serializers.Serializer):
    metadata = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("metadata",)

    def get_metadata(self, obj):
        try:
            extension = obj.userextension
            return extension.metadata
        except UserExtension.DoesNotExist:
            return {}

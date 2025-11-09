from rest_framework import serializers
from .models import EncryptedKey
from django.db import IntegrityError, transaction


class EncryptedKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = EncryptedKey
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        certificate = data["certificate"]
        if not certificate.is_valid:
            raise serializers.ValidationError(
                "Container keys should only be created for valid certificates"
            )
        return data

    def create(self, *args, **kwargs):
        try:
            return super().create(*args, **kwargs)
        except IntegrityError as e:
            raise serializers.ValidationError(
                {"non_field_errors": [f"Database Integrity Error: {str(e)}"]}
            )


class EncryptedKeyDetailSerializer(serializers.ModelSerializer):
    """To be used with UpdateEncryptedKeyListSerializer. See
    https://www.django-rest-framework.org/api-guide/serializers/#customizing-multiple-update
    """

    id = serializers.IntegerField()

    class Meta:
        model = EncryptedKey
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        keys = list(data.keys())
        # Only `is_valid` and `encrypted_key_base64` are allowed to be edited
        if set(keys) != {"is_valid", "encrypted_key_base64"}:
            raise serializers.ValidationError(
                "User can only invalidate a container key and overwrite its value"
            )
        # `is_valid` is only allowed to become False
        if data["is_valid"]:
            raise serializers.ValidationError(
                "User can only invalidate a container key and overwrite its value"
            )
        return data


class CreateEncryptedKeyListSerializer(serializers.ListSerializer):
    child = EncryptedKeySerializer()

    def create(self, validated_data):
        objects = []
        for entry in validated_data:
            objects.append(EncryptedKey(**entry))

        try:
            with transaction.atomic():
                return EncryptedKey.objects.bulk_create(objects)
        except IntegrityError as e:
            raise serializers.ValidationError(
                {"non_field_errors": [f"Database Integrity Error: {str(e)}"]}
            )


class UpdateEncryptedKeyListSerializer(serializers.ListSerializer):
    child = EncryptedKeyDetailSerializer()

    def update(self, instance, validated_data):
        if len(instance) != len(validated_data):
            raise serializers.ValidationError("Not all requested encrypted keys exist.")

        instance_mapping = {obj.id: obj for obj in instance}
        data_mapping = {item["id"]: item for item in validated_data}

        for pk in data_mapping.keys():
            obj = instance_mapping[pk]
            obj.is_valid = data_mapping[pk]["is_valid"]
            obj.encrypted_key_base64 = data_mapping[pk]["encrypted_key_base64"]
        try:
            with transaction.atomic():
                return EncryptedKey.objects.bulk_update(
                    instance_mapping.values(), ["is_valid", "encrypted_key_base64"]
                )
        except IntegrityError as e:
            raise serializers.ValidationError(
                {"non_field_errors": [f"Database Integrity Error: {str(e)}"]}
            )

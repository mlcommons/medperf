from rest_framework import serializers
from .models import Model
from mlcube.serializers import MlCubeSerializer
from asset.serializers import AssetSerializer
from mlcube.models import MlCube
from asset.models import Asset
from django.db import transaction


class ModelSerializer(serializers.ModelSerializer):
    container = MlCubeSerializer(required=False, allow_null=True)
    asset = AssetSerializer(required=False, allow_null=True)

    class Meta:
        model = Model
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, attrs):
        model_type = attrs.get("type")
        container = attrs.get("container")
        asset = attrs.get("asset")

        if model_type == "CONTAINER":
            if not container:
                raise serializers.ValidationError("Container data required.")
            if asset:
                raise serializers.ValidationError("Asset must not be provided.")
            nested_data = container
        elif model_type == "ASSET":
            if not asset:
                raise serializers.ValidationError("Asset data required.")
            if container:
                raise serializers.ValidationError("Container must not be provided.")
            nested_data = asset

        state = attrs.get("state", "DEVELOPMENT")
        nested_state = nested_data.get("state", "DEVELOPMENT")
        if state != nested_state:
            raise serializers.ValidationError(
                "Model state must match the state of its container or asset."
            )

        is_valid = attrs.get("is_valid", True)
        nested_is_valid = nested_data.get("is_valid", True)
        if is_valid != nested_is_valid:
            raise serializers.ValidationError(
                "Model validity must match the validity of its container or asset."
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        container_data = validated_data.pop("container", None)
        asset_data = validated_data.pop("asset", None)

        if container_data:
            container = MlCube.objects.create(
                **container_data, owner=validated_data["owner"]
            )
            validated_data["container"] = container

        if asset_data:
            asset = Asset.objects.create(**asset_data, owner=validated_data["owner"])
            validated_data["asset"] = asset

        return Model.objects.create(**validated_data)


class ModelDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Model
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        if self.instance.state == "OPERATION":
            editable_fields = [
                "is_valid",
                "user_metadata",
            ]
            for k, v in data.items():
                if k not in editable_fields:
                    if v != getattr(self.instance, k):
                        raise serializers.ValidationError(
                            "User cannot update non editable fields in Operation mode"
                        )

        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        if instance.type == "CONTAINER":
            instance.container.state = validated_data.get(
                "state", instance.container.state
            )
            instance.container.is_valid = validated_data.get(
                "is_valid", instance.container.is_valid
            )
            instance.container.save()
        if instance.type == "ASSET":
            instance.asset.state = validated_data.get("state", instance.asset.state)
            instance.asset.is_valid = validated_data.get(
                "is_valid", instance.asset.is_valid
            )
            instance.asset.save()

        return super().update(instance, validated_data)

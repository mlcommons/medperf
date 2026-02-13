from rest_framework import serializers
from .models import Model


class ModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Model
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        model_type = data.get("type")
        container = data.get("container")
        asset = data.get("asset")

        if model_type == "CONTAINER":
            if not container:
                raise serializers.ValidationError(
                    "Container must be set for CONTAINER type models."
                )
            if asset:
                raise serializers.ValidationError(
                    "Asset must not be set for CONTAINER type models."
                )
        elif model_type == "ASSET":
            if not asset:
                raise serializers.ValidationError(
                    "Asset must be set for FILE type models."
                )
            if container:
                raise serializers.ValidationError(
                    "Container must not be set for FILE type models."
                )
        else:
            raise serializers.ValidationError("Invalid model type.")

        if (
            "state" in data
            and data["state"] == "OPERATION"
            and model_type == "CONTAINER"
            and container.state == "DEVELOPMENT"
        ):
            raise serializers.ValidationError(
                "User cannot mark a model as operational"
                " if its container is not operational"
            )
        if (
            "state" in data
            and data["state"] == "OPERATION"
            and model_type == "ASSET"
            and asset.state == "DEVELOPMENT"
        ):
            raise serializers.ValidationError(
                "User cannot mark a model as operational"
                " if its asset is not operational"
            )
        return data


class ModelDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Model
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate_state(self, state):
        if state == "OPERATION" and self.instance.state != "OPERATION":
            if (
                self.instance.type == "CONTAINER"
                and self.instance.container.state == "DEVELOPMENT"
            ):
                raise serializers.ValidationError(
                    "User cannot mark a model as operational"
                    " if its container is not operational"
                )
            if (
                self.instance.type == "ASSET"
                and self.instance.asset.state == "DEVELOPMENT"
            ):
                raise serializers.ValidationError(
                    "User cannot mark a model as operational"
                    " if its asset is not operational"
                )

        return state

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

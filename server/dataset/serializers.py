from rest_framework import serializers
from .models import Dataset
from user.serializers import UserSerializer


class DatasetFullSerializer(serializers.ModelSerializer):
    """A private serializer. used for users who are permitted to see
    "sensitive" information. This serializer is also used for POST"""

    class Meta:
        model = Dataset
        fields = "__all__"
        read_only_fields = ["owner", "state"]


class DatasetPublicSerializer(serializers.ModelSerializer):
    """A restrictive serializer"""

    class Meta:
        model = Dataset
        exclude = ["owner", "report"]


class DatasetDetailSerializer(serializers.ModelSerializer):
    """This is a private serializer like DatasetFullSerializer"""

    class Meta:
        model = Dataset
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate_state(self, state):
        # NOTE: this is checking the uniqueness of generated_uid across
        #       operational datasets. This check relies on the fact that
        #       such a constraint can only be violated by updating the state.
        #       updating the generated_uid while state is OPERATION is already
        #       not allowed.
        # NOTE: This is written explicitely although the constraint is also
        #       defined in models.py. The reason is that DRF doesn't translate
        #       uniqueness constraint correctly, causing a 500 server error
        #       if the check was left to be done by the database.
        if state == "OPERATION" and self.instance.state == "DEVELOPMENT":
            constraint = (
                Dataset.objects.all()
                .filter(state="OPERATION", generated_uid=self.instance.generated_uid)
                .exists()
            )
            if constraint:
                raise serializers.ValidationError(
                    "An Operational dataset with the same generated UID already exists"
                )
        return state

    def validate(self, data):
        if self.instance.state == "OPERATION":
            editable_fields = ["is_valid", "user_metadata"]
            for k, v in data.items():
                if k not in editable_fields:
                    if v != getattr(self.instance, k):
                        raise serializers.ValidationError(
                            "User cannot update non editable fields in Operation mode"
                        )
        return data


class DatasetWithOwnerInfoSerializer(serializers.ModelSerializer):
    """This is needed for training to get datasets and their owners
    with one API call."""

    owner = UserSerializer()

    class Meta:
        model = Dataset
        fields = ["id", "owner"]

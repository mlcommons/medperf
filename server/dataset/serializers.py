from rest_framework import serializers
from .models import Dataset
from user.serializers import UserSerializer


def validate_exactly_one_preparation(data: dict):
    no_data_prep_provided = (
        data.get("data_preparation_mlcube") is None
        and data.get("data_preparation_workflow") is None
    )
    multiple_data_prep_provided = (
        data.get("data_preparation_mlcube") is not None
        and data.get("data_preparation_workflow") is not None
    )
    if no_data_prep_provided or multiple_data_prep_provided:
        raise serializers.ValidationError(
            "Exactly one of 'data_preparation_mlcube' or 'data_preparation_workflow' must be provided to register a Benchmark"
        )


class DatasetFullSerializer(serializers.ModelSerializer):
    """A private serializer. used for users who are permitted to see
    "sensitive" information. This serializer is also used for POST"""

    class Meta:
        model = Dataset
        fields = "__all__"
        read_only_fields = ["owner", "state"]

    def validate(self, data):
        validate_exactly_one_preparation(data)


class DatasetPublicSerializer(serializers.ModelSerializer):
    """A restrictive serializer"""

    class Meta:
        model = Dataset
        exclude = ["owner", "report"]

    def validate(self, data):
        validate_exactly_one_preparation(data)


class DatasetDetailSerializer(serializers.ModelSerializer):
    """This is a private serializer like DatasetFullSerializer"""

    class Meta:
        model = Dataset
        fields = "__all__"
        read_only_fields = ["owner"]

    def _validate_guid(self, data):
        # NOTE: this is checking the uniqueness of generated_uid across
        #       operational datasets. This check relies on the fact that
        #       such a constraint can only be violated by updating the state.
        #       updating the generated_uid while state is OPERATION is already
        #       not allowed.
        # NOTE: This is written explicitely although the constraint is also
        #       defined in models.py. The reason is that DRF doesn't translate
        #       uniqueness constraint correctly, causing a 500 server error
        #       if the check was left to be done by the database.
        if (
            data.get("state")
            and data["state"] == "OPERATION"
            and self.instance.state == "DEVELOPMENT"
        ):
            constraint = (
                Dataset.objects.all()
                .filter(
                    state="OPERATION",
                    generated_uid=data.get(
                        "generated_uid", self.instance.generated_uid
                    ),
                )
                .exists()
            )
            if constraint:
                raise serializers.ValidationError(
                    "An Operational dataset with the same "
                    "generated UID already exists"
                )

    def validate(self, data):
        if self.instance.state == "OPERATION":
            editable_fields = ["is_valid", "user_metadata"]
            for k, v in data.items():
                value_changed = v != getattr(self.instance, k)
                if k not in editable_fields and value_changed:
                    raise serializers.ValidationError(
                        "User cannot update non editable fields in Operation mode"
                    )
        self._validate_guid(data)
        validate_exactly_one_preparation(data)
        return data


class DatasetWithOwnerInfoSerializer(serializers.ModelSerializer):
    """This is needed when getting datasets and their owners
    with one API call."""

    owner = UserSerializer()

    class Meta:
        model = Dataset
        fields = ["id", "owner"]

    def validate(self, data):
        validate_exactly_one_preparation(data)

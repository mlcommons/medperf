from rest_framework import serializers
from .models import TrainingExperiment
from signing.interface import generate_key_pair
from django.utils import timezone


class WriteTrainingExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingExperiment
        exclude = ["private_key"]
        read_only_fields = [
            "owner",
            "private_key",
            "public_key",
            "approved_at",
            "approval_status",
        ]

    def validate(self, data):
        owner = self.context["request"].user
        pending_experiments = TrainingExperiment.objects.filter(
            owner=owner, approval_status="PENDING"
        )
        if len(pending_experiments) > 0:
            raise serializers.ValidationError(
                "User can own at most one pending experiment"
            )
        return data

    def save(self, **kwargs):
        super().save(**kwargs)

        # TODO: move key generation after admin approval? YES
        # TODO: use atomic transaction
        private_key_id, public_key = generate_key_pair(self.instance.id)
        self.instance.private_key = private_key_id
        self.instance.public_key = public_key
        self.instance.save()

        return self.instance


class ReadTrainingExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingExperiment
        exclude = ["private_key"]

    def update(self, instance, validated_data):
        # TODO: seems buggy
        if (
            instance.approval_status != "PENDING"
            and "approval_status" in validated_data
            and validated_data["approval_status"] == "APPROVED"
        ):
            instance.approved_at = timezone.now()
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance

    def validate(self, data):
        if "approval_status" in data:
            if (
                data["approval_status"] == "PENDING"
                and self.instance.approval_status != "PENDING"
            ):
                pending_experiments = TrainingExperiment.objects.filter(
                    owner=self.instance.owner, approval_status="PENDING"
                )
                if len(pending_experiments) > 0:
                    raise serializers.ValidationError(
                        "User can own at most one pending experiment"
                    )

        editable_fields = [
            "is_valid",
            "user_metadata",
            "approval_status",
            "demo_dataset_tarball_url",
        ]
        if self.instance.state == "DEVELOPMENT":
            editable_fields.append("state")

        for k, v in data.items():
            if k not in editable_fields:
                if v != getattr(self.instance, k):
                    raise serializers.ValidationError(
                        "User cannot update non editable fields"
                    )
        if (
            "state" in data
            and data["state"] == "OPERATION"
            and self.instance.state == "DEVELOPMENT"
        ):
            # TODO: check if there is an approved aggregator other wise raise
            # and at least one approved dataset??
            pass
        return data

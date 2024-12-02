from rest_framework import serializers
from django.utils import timezone
from training.models import TrainingExperiment
from dataset.models import Dataset

from .models import ExperimentDataset
from utils.associations import (
    validate_approval_status_on_creation,
    validate_approval_status_on_update,
)


def is_approved_participant(training_exp, dataset):
    # training_exp event status
    event = training_exp.event
    if not event or event.finished:
        return

    # TODO: modify when we use dataset labels
    # TODO: is there a cleaner way? We are making assumptions on the json field structure
    participants_list = event.participants.values()
    return dataset.owner.email in participants_list


class ExperimentDatasetListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentDataset
        read_only_fields = ["initiated_by", "approved_at"]
        fields = "__all__"

    def validate(self, data):
        tid = self.context["request"].data.get("training_exp")
        dataset = self.context["request"].data.get("dataset")
        approval_status = self.context["request"].data.get("approval_status", "PENDING")

        training_exp = TrainingExperiment.objects.get(pk=tid)

        # training_exp approval status
        training_exp_approval_status = training_exp.approval_status
        if training_exp_approval_status != "APPROVED":
            raise serializers.ValidationError(
                "Association requests can be made only on an approved training experiment"
            )

        # dataset state
        dataset_obj = Dataset.objects.get(pk=dataset)
        dataset_state = dataset_obj.state
        if dataset_state != "OPERATION":
            raise serializers.ValidationError(
                "Association requests can be made only on an operational dataset"
            )

        # dataset prep mlcube
        if dataset_obj.data_preparation_mlcube != training_exp.data_preparation_mlcube:
            raise serializers.ValidationError(
                "Dataset association request can be made only if the dataset"
                " was prepared with the training experiment's data preparation MLCube"
            )

        # approval status
        last_training_expdataset = (
            ExperimentDataset.objects.filter(training_exp__id=tid, dataset__id=dataset)
            .order_by("-created_at")
            .first()
        )
        validate_approval_status_on_creation(last_training_expdataset, approval_status)

        return data

    def create(self, validated_data):
        approval_status = validated_data.get("approval_status", "PENDING")
        if approval_status != "PENDING":
            validated_data["approved_at"] = timezone.now()
        else:
            same_owner = (
                validated_data["dataset"].owner.id
                == validated_data["training_exp"].owner.id
            )
            if same_owner or is_approved_participant(
                validated_data["training_exp"], validated_data["dataset"]
            ):
                validated_data["approval_status"] = "APPROVED"
                validated_data["approved_at"] = timezone.now()
        return ExperimentDataset.objects.create(**validated_data)


class DatasetApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentDataset
        read_only_fields = ["initiated_by", "approved_at"]
        fields = [
            "approval_status",
            "initiated_by",
            "approved_at",
            "created_at",
            "modified_at",
        ]

    def validate(self, data):
        if not self.instance:
            raise serializers.ValidationError("No dataset association found")
        return data

    def validate_approval_status(self, cur_approval_status):
        last_approval_status = self.instance.approval_status
        initiated_user = self.instance.initiated_by
        current_user = self.context["request"].user
        validate_approval_status_on_update(
            last_approval_status, cur_approval_status, initiated_user, current_user
        )

        event = self.instance.training_exp.event
        if event and not event.finished:
            raise serializers.ValidationError(
                "User cannot approve or reject an association when the experiment is ongoing"
            )
        return cur_approval_status

    def update(self, instance, validated_data):
        if "approval_status" in validated_data:
            if validated_data["approval_status"] != instance.approval_status:
                instance.approval_status = validated_data["approval_status"]
                if instance.approval_status != "PENDING":
                    instance.approved_at = timezone.now()
        instance.save()
        return instance


class TrainingExperimentListofDatasetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentDataset
        fields = ["dataset", "approval_status", "created_at"]

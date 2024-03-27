from rest_framework import serializers
from django.utils import timezone
from training.models import TrainingExperiment
from dataset.models import Dataset

from .models import ExperimentDataset
from signing.interface import verify_dataset_csr, sign_csr


class ExperimentDatasetListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentDataset
        read_only_fields = ["initiated_by", "approved_at", "certificate"]
        fields = "__all__"

    def validate(self, data):
        exp_id = self.context["request"].data.get("training_exp")
        dataset = self.context["request"].data.get("dataset")
        approval_status = self.context["request"].data.get("approval_status")
        csr = self.context["request"].data.get("signing_request")

        training_exp = TrainingExperiment.objects.get(pk=exp_id)
        training_exp_state = training_exp.state

        if training_exp_state != "DEVELOPMENT":
            raise serializers.ValidationError(
                "Dataset Association requests can be made only "
                "on a development training experiment"
            )
        training_exp_approval_status = training_exp.approval_status
        if training_exp_approval_status != "APPROVED":
            raise serializers.ValidationError(
                "Association requests can be made only on an approved training experiment"
            )
        dataset_object = Dataset.objects.get(pk=dataset)
        dataset_state = dataset_object.state
        if dataset_state != "OPERATION":
            raise serializers.ValidationError(
                "Association requests can be made only on an operational dataset"
            )
        last_experiment_dataset = (
            ExperimentDataset.objects.filter(
                training_exp__id=exp_id, dataset__id=dataset
            )
            .order_by("-created_at")
            .first()
        )
        if not last_experiment_dataset:
            if approval_status != "PENDING":
                raise serializers.ValidationError(
                    "User can approve or reject association request only if there are prior requests"
                )
        else:
            if approval_status == "PENDING":
                if last_experiment_dataset.approval_status != "REJECTED":
                    raise serializers.ValidationError(
                        "User can create a new request only if prior request is rejected"
                    )
            elif approval_status == "APPROVED":
                raise serializers.ValidationError(
                    "User cannot create an approved association request"
                )
            # approval_status == "REJECTED":
            else:
                if last_experiment_dataset.approval_status != "APPROVED":
                    raise serializers.ValidationError(
                        "User can reject request only if prior request is approved"
                    )

        valid_csr, reason = verify_dataset_csr(csr, dataset_object, training_exp)
        if not valid_csr:
            raise serializers.ValidationError(reason)

        return data

    def create(self, validated_data):
        approval_status = validated_data.get("approval_status", "PENDING")
        if approval_status != "PENDING":
            validated_data["approved_at"] = timezone.now()
        else:
            if (
                validated_data["dataset"].owner.id
                == validated_data["training_exp"].owner.id
            ):
                validated_data["approval_status"] = "APPROVED"
                validated_data["approved_at"] = timezone.now()
                csr = validated_data["signing_request"]
                certificate = sign_csr(csr, validated_data["training_exp"])
                validated_data["certificate"] = certificate
        return ExperimentDataset.objects.create(**validated_data)


class DatasetApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentDataset
        read_only_fields = ["initiated_by", "approved_at", "certificate"]
        fields = [
            "approval_status",
            "initiated_by",
            "approved_at",
            "created_at",
            "modified_at",
            "certificate",
        ]

    def validate(self, data):
        if not self.instance:
            raise serializers.ValidationError("No dataset association found")
        last_approval_status = self.instance.approval_status
        cur_approval_status = data["approval_status"]
        if last_approval_status != "PENDING":
            raise serializers.ValidationError(
                "User can approve or reject only a pending request"
            )
        initiated_user = self.instance.initiated_by
        current_user = self.context["request"].user
        if (
            last_approval_status != cur_approval_status
            and cur_approval_status == "APPROVED"
        ):
            if current_user.id == initiated_user.id:
                raise serializers.ValidationError(
                    "Same user cannot approve the association request"
                )
        return data

    def update(self, instance, validated_data):
        instance.approval_status = validated_data["approval_status"]
        if instance.approval_status != "PENDING":
            instance.approved_at = timezone.now()
        if instance.approval_status == "APPROVED":
            csr = instance.signing_request
            certificate = sign_csr(csr, self.instance.training_exp.id)
            instance.certificate = certificate
        instance.save()
        return instance

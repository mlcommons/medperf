from rest_framework import serializers
from django.utils import timezone
from training.models import TrainingExperiment
from django.conf import settings

from .models import ExperimentCA
from utils.associations import (
    validate_approval_status_on_creation,
    validate_approval_status_on_update,
)


class ExperimentCAListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentCA
        read_only_fields = ["initiated_by", "approved_at"]
        fields = "__all__"

    def validate(self, data):
        tid = self.context["request"].data.get("training_exp")
        ca = self.context["request"].data.get("ca")
        approval_status = self.context["request"].data.get("approval_status", "PENDING")

        training_exp = TrainingExperiment.objects.get(pk=tid)

        # training_exp approval status
        training_exp_approval_status = training_exp.approval_status
        if training_exp_approval_status != "APPROVED":
            raise serializers.ValidationError(
                "Association requests can be made only on an approved training experiment"
            )

        # training_exp event status
        event = training_exp.event
        if event and not event.finished:
            raise serializers.ValidationError(
                "The training experiment does not currently accept associations"
            )

        # An already approved ca
        exp_ca = training_exp.ca
        if exp_ca and exp_ca.id != ca:
            raise serializers.ValidationError(
                "The training experiment already has an ca"
            )

        # approval status
        last_experiment_ca = (
            ExperimentCA.objects.filter(training_exp__id=tid, ca__id=ca)
            .order_by("-created_at")
            .first()
        )
        validate_approval_status_on_creation(last_experiment_ca, approval_status)

        return data

    def create(self, validated_data):
        approval_status = validated_data.get("approval_status", "PENDING")
        if approval_status != "PENDING":
            validated_data["approved_at"] = timezone.now()
        else:
            same_owner = (
                validated_data["ca"].owner.id == validated_data["training_exp"].owner.id
            )
            is_main_ca = validated_data["ca"].name == settings.CA_NAME
            if same_owner or is_main_ca:
                validated_data["approval_status"] = "APPROVED"
                validated_data["approved_at"] = timezone.now()
        return ExperimentCA.objects.create(**validated_data)


class CAApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperimentCA
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
            raise serializers.ValidationError("No ca association found")
        # check if there is already an approved ca
        exp_ca = self.instance.training_exp.ca
        if exp_ca and exp_ca.id != self.instance.ca.id:
            raise serializers.ValidationError(
                "The training experiment already has an ca"
            )
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

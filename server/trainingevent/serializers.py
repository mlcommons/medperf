from rest_framework import serializers
from .models import TrainingEvent
from training.models import TrainingExperiment
from django.utils import timezone


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingEvent
        fields = "__all__"
        read_only_fields = ["finished", "finished_at", "report", "owner"]

    def validate(self, data):
        training_exp = TrainingExperiment.objects.get(pk=data["training_exp"])
        if training_exp.approval_status != "APPROVED":
            raise serializers.ValidationError(
                "User cannot create an event unless the experiment is approved"
            )
        prev_event = training_exp.event
        if prev_event and not training_exp.event.finished:
            raise serializers.ValidationError(
                "User cannot create a new event unless the previous event has finished"
            )
        aggregator = training_exp.aggregator
        if not aggregator:
            raise serializers.ValidationError(
                "User cannot create a new event if the experiment has no aggregator"
            )
        plan = training_exp.plan
        if plan is None:
            raise serializers.ValidationError(
                "User cannot create a new event if the experiment has no plan"
            )

        return data


class EventDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingEvent
        fields = "__all__"
        read_only_fields = [
            "finished_at",
            "training_exp",
            "participants",
            "finished",
            "owner",
        ]

    def validate(self, data):
        if self.instance.finished:
            raise serializers.ValidationError("User cannot edit a finished event")
        return data

    def update(self, instance, validated_data):
        if "report" in validated_data:
            instance.report = validated_data["report"]
            instance.finished = True
            instance.finished_at = timezone.now()
        instance.save()
        return instance

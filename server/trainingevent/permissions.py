from rest_framework.permissions import BasePermission
from .models import TrainingEvent, TrainingExperiment


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsExpOwner(BasePermission):
    def get_object(self, tid):
        try:
            return TrainingExperiment.objects.get(pk=tid)
        except TrainingExperiment.DoesNotExist:
            return None

    def get_event_object(self, pk):
        try:
            return TrainingEvent.objects.get(pk=pk)
        except TrainingEvent.DoesNotExist:
            return None

    def has_permission(self, request, view):
        if request.method == "POST":
            tid = request.data.get("training_exp", None)
        else:
            pk = view.kwargs.get("pk", None)
            if not pk:
                return False
            event = self.get_event_object(pk)
            if not event:
                return False
            tid = event.training_exp.id

        if not tid:
            return False
        training_exp = self.get_object(tid)
        if not training_exp:
            return False
        if training_exp.owner.id == request.user.id:
            return True
        else:
            return False


class IsAggregatorOwner(BasePermission):
    def get_object(self, pk):
        try:
            return TrainingEvent.objects.get(pk=pk)
        except TrainingEvent.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        event = self.get_object(pk)
        if not event:
            return False
        aggregator = event.training_exp.aggregator
        if not aggregator:
            return False

        if aggregator.owner.id == request.user.id:
            return True
        else:
            return False

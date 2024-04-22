from rest_framework.permissions import BasePermission
from .models import TrainingExperiment


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsExpOwner(BasePermission):
    def get_object(self, tid):
        try:
            return TrainingExperiment.objects.get(pk=tid)
        except TrainingExperiment.DoesNotExist:
            return None

    def has_permission(self, request, view):
        tid = view.kwargs.get("tid", None)
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
    def get_object(self, tid):
        try:
            return TrainingExperiment.objects.get(pk=tid)
        except TrainingExperiment.DoesNotExist:
            return None

    def has_permission(self, request, view):
        tid = view.kwargs.get("tid", None)
        if not tid:
            return False
        training_exp = self.get_object(tid)
        if not training_exp:
            return False
        aggregator = training_exp.aggregator
        if not aggregator:
            return False
        if aggregator.owner.id == request.user.id:
            return True
        else:
            return False

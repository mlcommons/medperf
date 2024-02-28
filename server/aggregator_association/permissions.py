from rest_framework.permissions import BasePermission
from training.models import TrainingExperiment
from aggregator.models import Aggregator


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsAggregatorOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Aggregator.objects.get(pk=pk)
        except Aggregator.DoesNotExist:
            return None

    def has_permission(self, request, view):
        if request.method == "POST":
            pk = request.data.get("aggregator", None)
        else:
            pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        aggregator = self.get_object(pk)
        if not aggregator:
            return False
        if aggregator.owner.id == request.user.id:
            return True
        else:
            return False


class IsExpOwner(BasePermission):
    def get_object(self, pk):
        try:
            return TrainingExperiment.objects.get(pk=pk)
        except TrainingExperiment.DoesNotExist:
            return None

    def has_permission(self, request, view):
        if request.method == "POST":
            pk = request.data.get("training_exp", None)
        else:
            pk = view.kwargs.get("tid", None)
        if not pk:
            return False
        training_exp = self.get_object(pk)
        if not training_exp:
            return False
        if training_exp.owner.id == request.user.id:
            return True
        else:
            return False

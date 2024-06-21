from rest_framework.permissions import BasePermission
from training.models import TrainingExperiment
from dataset.models import Dataset


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsDatasetOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Dataset.objects.get(pk=pk)
        except Dataset.DoesNotExist:
            return None

    def has_permission(self, request, view):
        if request.method == "POST":
            pk = request.data.get("dataset", None)
        else:
            pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        dataset = self.get_object(pk)
        if not dataset:
            return False
        if dataset.owner.id == request.user.id:
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
        training_experiment = self.get_object(pk)
        if not training_experiment:
            return False
        if training_experiment.owner.id == request.user.id:
            return True
        else:
            return False

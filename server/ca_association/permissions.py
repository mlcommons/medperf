from rest_framework.permissions import BasePermission
from training.models import TrainingExperiment
from ca.models import CA


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsCAOwner(BasePermission):
    def get_object(self, pk):
        try:
            return CA.objects.get(pk=pk)
        except CA.DoesNotExist:
            return None

    def has_permission(self, request, view):
        if request.method == "POST":
            pk = request.data.get("ca", None)
        else:
            pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        ca = self.get_object(pk)
        if not ca:
            return False
        if ca.owner.id == request.user.id:
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

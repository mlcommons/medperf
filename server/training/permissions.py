from rest_framework.permissions import BasePermission
from .models import TrainingExperiment


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsExpOwner(BasePermission):
    def get_object(self, pk):
        try:
            return TrainingExperiment.objects.get(pk=pk)
        except TrainingExperiment.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        training_exp = self.get_object(pk)
        if not training_exp:
            return False
        if training_exp.owner.id == request.user.id:
            return True
        else:
            return False

from rest_framework.permissions import BasePermission
from .models import Dataset


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

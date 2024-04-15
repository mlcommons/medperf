from rest_framework.permissions import BasePermission
from mlcube.models import MlCube
from dataset.models import Dataset


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsOwnUser(BasePermission):
    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        if pk == request.user.id:
            return True
        else:
            return False

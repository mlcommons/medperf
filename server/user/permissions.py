from rest_framework.permissions import BasePermission
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


class IsOwnerOfUsedMLCube(BasePermission):
    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False

        user_datasets_using_owned_mlcube = Dataset.objects.filter(
            owner=pk, data_preparation_mlcube__owner=request.user
        )

        return len(user_datasets_using_owned_mlcube)

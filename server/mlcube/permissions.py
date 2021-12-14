from rest_framework.permissions import BasePermission
from .models import MlCube


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsMlCubeOwner(BasePermission):
    def get_object(self, pk):
        try:
            return MlCube.objects.get(pk=pk)
        except MlCube.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        mlcube = self.get_object(pk)
        if not mlcube:
            return False
        if mlcube.owner.id == request.user.id:
            return True
        else:
            return False

from rest_framework.permissions import BasePermission
from mlcube.models import MlCube
from .models import MlCubeKey


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsKeyOwner(BasePermission):
    def get_object(self, pk):
        try:
            return MlCubeKey.objects.get(pk=pk)
        except MlCubeKey.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        key = self.get_object(pk)
        if not key:
            return False
        if key.owner.id == request.user.id:
            return True
        else:
            return False


class IsContainersOwner(BasePermission):
    def get_containers_objects(self, pks):
        return MlCube.objects.filter(id__in=pks)

    def has_permission(self, request, view):
        pks = request.data.get("container", None)
        if not pks:
            return False
        if isinstance(pks, int):
            pks = [pks]
        containers = self.get_containers_objects(pks)
        for container in containers:
            if container.owner.id != request.user.id:
                return False
        return True

from rest_framework.permissions import BasePermission
from mlcube.models import MlCube
from .models import EncryptedKey


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsKeyOwnerForGet(BasePermission):
    def get_object(self, pk):
        try:
            return EncryptedKey.objects.get(pk=pk)
        except EncryptedKey.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if pk is None:
            return False

        key = self.get_object(pk)
        if key is None:
            return False

        if key.owner.id == request.user.id:
            return True
        else:
            return False


class IsKeyOwnerForPut(BasePermission):
    def get_objects(self, pk_list):
        return EncryptedKey.objects.filter(pk__in=pk_list)

    def has_permission(self, request, view):
        pk_list = []
        for entry in request.data:
            if "id" not in entry:
                return False
            pk_list.append(entry["id"])

        keys = self.get_objects(pk_list)

        for key in keys:
            if key.owner.id != request.user.id:
                return False
        return True


class IsContainerOwner(BasePermission):
    def get_containers_objects(self, container_pks):
        return MlCube.objects.filter(id__in=container_pks)

    def has_permission(self, request, view):
        container_pks = []
        for entry in request.data:
            if "container" not in entry:
                return False
            container_pks.append(entry["container"])

        containers = self.get_containers_objects(container_pks)
        for container in containers:
            if container.owner.id != request.user.id:
                return False
        return True

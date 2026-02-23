from rest_framework.permissions import BasePermission
from .models import Model
from asset.models import Asset
from mlcube.models import MlCube


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsModelOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Model.objects.get(pk=pk)
        except Model.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        model_obj = self.get_object(pk)
        if not model_obj:
            return False
        if model_obj.owner.id == request.user.id:
            return True
        else:
            return False


class IsAssetOrContainerOwner(BasePermission):
    def get_asset(self, asset_id):
        try:
            return Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            return None

    def get_container(self, container_id):
        try:
            return MlCube.objects.get(id=container_id)
        except MlCube.DoesNotExist:
            return None

    def has_permission(self, request, view):
        asset_id = request.data.get("asset", None)
        container_id = request.data.get("container", None)

        if asset_id:
            asset = self.get_asset(asset_id)
            if not asset:
                return False
            if asset.owner.id == request.user.id:
                return True
            else:
                return False
        elif container_id:
            container = self.get_container(container_id)
            if not container:
                return False
            if container.owner.id == request.user.id:
                return True
            else:
                return False
        else:
            return False

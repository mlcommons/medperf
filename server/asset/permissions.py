from rest_framework.permissions import BasePermission
from .models import Asset


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsAssetOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Asset.objects.get(pk=pk)
        except Asset.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        asset = self.get_object(pk)
        if not asset:
            return False
        if asset.owner.id == request.user.id:
            return True
        else:
            return False

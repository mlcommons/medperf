from rest_framework.permissions import BasePermission
from .models import Model


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

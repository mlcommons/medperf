from rest_framework.permissions import BasePermission
from mlcube.models import MlCube
from medperf.permissions import IsOwnerOfAnotherObject


class IsModelOwnerForPost(IsOwnerOfAnotherObject):
    @property
    def another_object(self):
        return MlCube

    def has_permission(self, request, view):
        if request.method != "POST":
            return False

        pk = view.kwargs.get("model_id", None)

        return self.is_owner_of_another_object(pk=pk, request=request)


class IsDataOwnerForGet(BasePermission):
    def has_permission(self, request, view):
        return request.method == "GET"

    def has_object_permission(self, request, view, obj):
        if request.method != "GET":
            return False

        try:
            return obj.data_owner.id == request.user.id
        except AttributeError:
            return False

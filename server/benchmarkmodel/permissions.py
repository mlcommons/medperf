from rest_framework.permissions import BasePermission
from benchmark.models import Benchmark
from model.models import Model


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
        if request.method == "POST":
            pk = request.data.get("model", None)
        else:
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


class IsBenchmarkOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            return None

    def has_permission(self, request, view):
        if request.method == "POST":
            pk = request.data.get("benchmark", None)
        else:
            pk = view.kwargs.get("bid", None)
        if not pk:
            return False
        benchmark = self.get_object(pk)
        if not benchmark:
            return False
        if benchmark.owner.id == request.user.id:
            return True
        else:
            return False

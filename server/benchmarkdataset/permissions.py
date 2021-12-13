from rest_framework.permissions import BasePermission
from benchmark.models import Benchmark
from dataset.models import Dataset


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsDatasetOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Dataset.objects.get(pk=pk)
        except Dataset.DoesNotExist:
            raise None

    def has_permission(self, request, view):
        if request.method == "POST":
            pk = request.data.get("dataset", None)
        else:
            pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        dataset = self.get_object(pk)
        if not dataset:
            return False
        if dataset.owner.id == request.user.id:
            return True
        else:
            return False


class IsBenchmarkOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            raise None

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

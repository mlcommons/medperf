from rest_framework.permissions import BasePermission
from benchmark.models import Benchmark
from dataset.models import Dataset
from .models import ModelResult


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsResultOwner(BasePermission):
    def get_object(self, pk):
        try:
            return ModelResult.objects.get(pk=pk)
        except ModelResult.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        result = self.get_object(pk)
        if not result:
            return False
        if result.owner.id == request.user.id:
            return True
        else:
            return False


class IsDatasetOwner(BasePermission):
    def get_result_object(self, pk):
        try:
            return ModelResult.objects.get(pk=pk)
        except ModelResult.DoesNotExist:
            raise None

    def get_dataset_object(self, pk):
        try:
            return Dataset.objects.get(pk=pk)
        except Dataset.DoesNotExist:
            raise None

    def has_permission(self, request, view):
        if request.method == "POST":
            pk = request.data.get("dataset", None)
        else:
            result_pk = view.kwargs.get("pk", None)
            result = get_result_object(result_pk)
            if not result:
                return False
            pk = result.dataset
        if not pk:
            return False
        dataset = self.get_dataset_object(pk)
        if not dataset:
            return False
        if dataset.owner.id == request.user.id:
            return True
        else:
            return False

class IsBenchmarkOwner(BasePermission):
    def get_result_object(self, pk):
        try:
            return ModelResult.objects.get(pk=pk)
        except ModelResult.DoesNotExist:
            raise None

    def get_benchmark_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            raise None

    def has_permission(self, request, view):
        if request.method == "GET":
            result_pk = view.kwargs.get("pk", None)
            result = get_result_object(result_pk)
            if not result:
                return False
            pk = result.benchmark
        if not pk:
            return False
        benchmark = self.get_benchmark_object(pk)
        if not benchmark:
            return False
        if benchmark.owner.id == request.user.id:
            return True
        else:
            return False

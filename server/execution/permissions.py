from rest_framework.permissions import BasePermission
from benchmark.models import Benchmark
from dataset.models import Dataset
from .models import Execution


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsExecutionOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Execution.objects.get(pk=pk)
        except Execution.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        execution = self.get_object(pk)
        if not execution:
            return False
        if execution.owner.id == request.user.id:
            return True
        else:
            return False


class IsDatasetOwner(BasePermission):
    def get_execution_object(self, pk):
        try:
            return Execution.objects.get(pk=pk)
        except Execution.DoesNotExist:
            return None

    def get_dataset_object(self, pk):
        try:
            return Dataset.objects.get(pk=pk)
        except Dataset.DoesNotExist:
            return None

    def has_permission(self, request, view):
        if request.method == "POST":
            pk = request.data.get("dataset", None)
        else:
            execution_pk = view.kwargs.get("pk", None)
            execution = self.get_execution_object(execution_pk)
            if not execution:
                return False
            pk = execution.dataset.id
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
    def get_execution_object(self, pk):
        try:
            return Execution.objects.get(pk=pk)
        except Execution.DoesNotExist:
            return None

    def get_benchmark_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            return None

    def has_permission(self, request, view):
        if request.method == "GET":
            execution_pk = view.kwargs.get("pk", None)
            execution = self.get_execution_object(execution_pk)
            if not execution:
                return False
            pk = execution.benchmark.id
        if not pk:
            return False
        benchmark = self.get_benchmark_object(pk)
        if not benchmark:
            return False
        if benchmark.owner.id == request.user.id:
            return True
        else:
            return False

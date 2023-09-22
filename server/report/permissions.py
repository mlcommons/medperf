from rest_framework.permissions import BasePermission
from .models import Report
from benchmark.models import Benchmark
from mlcube.models import MlCube


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsReportOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        report = self.get_object(pk)
        if not report:
            return False
        if report.owner.id == request.user.id:
            return True
        else:
            return False


class IsBenchmarkOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return None

    def get_benchmark_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        report = self.get_object(pk)
        if not report:
            return False

        benchmark_id = report.benchmark.id
        if not benchmark_id:
            return False
        benchmark = self.get_benchmark_object(benchmark_id)
        if not benchmark:
            return False
        if benchmark.owner.id == request.user.id:
            return True
        else:
            return False


class IsMlCubeOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return None

    def get_mlcube_object(self, pk):
        try:
            return MlCube.objects.get(pk=pk)
        except MlCube.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        report = self.get_object(pk)
        if not report:
            return False

        mlcube_id = report.data_preparation_mlcube.id
        if not mlcube_id:
            return False
        mlcube = self.get_mlcube_object(mlcube_id)
        if not mlcube:
            return False
        if mlcube.owner.id == request.user.id:
            return True
        else:
            return False

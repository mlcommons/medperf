from rest_framework.permissions import BasePermission
from benchmarkmodel.models import BenchmarkModel
from mlcube.models import MlCube
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated

class IsModelApprovedInBenchmark(BasePermission):
    def has_permission(self, request: Request, view):
        if request.method != "GET":
            return False

        benchmark_id = view.kwargs.get("benchmark_id")
        model_id = view.kwargs.get("model_id")

        try:
            benchmark_model_association = BenchmarkModel.objects.get(
                model_mlcube__id=model_id, benchmark__id=benchmark_id
            )
        except BenchmarkModel.DoesNotExist:
            return False
        return benchmark_model_association.approval_status == "APPROVED"


class IsModelOwner(BasePermission):
    def has_permission(self, request: Request, view):
        if request.method != "GET":
            return False

        model_id = view.kwargs.get("model_id")

        try:
            model = MlCube.objects.get(pk=model_id)
        except BenchmarkModel.DoesNotExist:
            return False
        return model.owner.id == request.user.id


class IsAuthenticatedAndIsPostRequest(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method != "POST":
            return False

        return super().has_permission(request, view)

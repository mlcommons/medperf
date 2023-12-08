from rest_framework.permissions import BasePermission
from .models import Benchmark
from benchmarkdataset.models import BenchmarkDataset
from django.db.models import OuterRef, Subquery


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsBenchmarkOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        benchmark = self.get_object(pk)
        if not benchmark:
            return False
        if benchmark.owner.id == request.user.id:
            return True
        else:
            return False


# TODO: check effciency / database costs
class IsAssociatedDatasetOwner(BasePermission):
    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False

        if not request.user.is_authenticated:
            # This check is to prevent internal server error
            # since user.dataset_set is used below
            return False

        latest_datasets_assocs_status = (
            BenchmarkDataset.objects.all()
            .filter(benchmark__id=pk, dataset__id=OuterRef("id"))
            .order_by("-created_at")[:1]
            .values("approval_status")
        )

        user_associated_datasets = (
            request.user.dataset_set.all()
            .annotate(assoc_status=Subquery(latest_datasets_assocs_status))
            .filter(assoc_status="APPROVED")
        )

        if user_associated_datasets.exists():
            return True
        else:
            return False

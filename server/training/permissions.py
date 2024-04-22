from rest_framework.permissions import BasePermission
from .models import TrainingExperiment
from traindataset_association.models import ExperimentDataset
from django.db.models import OuterRef, Subquery


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsExpOwner(BasePermission):
    def get_object(self, pk):
        try:
            return TrainingExperiment.objects.get(pk=pk)
        except TrainingExperiment.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        training_exp = self.get_object(pk)
        if not training_exp:
            return False
        if training_exp.owner.id == request.user.id:
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
            ExperimentDataset.objects.all()
            .filter(training_exp__id=pk, dataset__id=OuterRef("id"))
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


class IsAggregatorOwner(BasePermission):
    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False

        if not request.user.is_authenticated:
            # This check is to prevent internal server error
            # since user.dataset_set is used below
            return False

        training_exp = TrainingExperiment.objects.get(pk=pk)
        aggregator = training_exp.aggregator
        if not aggregator:
            return False

        if aggregator.owner.id == request.user.id:
            return True
        else:
            return False

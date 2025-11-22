from __future__ import annotations
from rest_framework.permissions import BasePermission
from benchmarkmodel.models import BenchmarkModel
from .models import Certificate
from django.db.models import OuterRef, Subquery


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsCertificateOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Certificate.objects.get(pk=pk)
        except Certificate.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        certificate = self.get_object(pk)
        if not certificate:
            return False
        if certificate.owner.id == request.user.id:
            return True
        else:
            return False


# TODO: check effciency / database costs
class IsAssociatedModelOwner(BasePermission):
    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False

        if not request.user.is_authenticated:
            # This check is to prevent internal server error
            # since user.mlcube_set is used below
            return False

        latest_models_assocs_status = (
            BenchmarkModel.objects.all()
            .filter(benchmark__id=pk, model_mlcube__id=OuterRef("id"))
            .order_by("-created_at")[:1]
            .values("approval_status")
        )

        user_associated_models = (
            request.user.mlcube_set.all()
            .annotate(assoc_status=Subquery(latest_models_assocs_status))
            .filter(assoc_status="APPROVED")
        )

        if user_associated_models.exists():
            return True
        else:
            return False

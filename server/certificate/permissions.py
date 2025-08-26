from __future__ import annotations
from typing import TYPE_CHECKING
from rest_framework.permissions import BasePermission
from benchmarkmodel.models import BenchmarkModel
from mlcube.models import MlCube
from rest_framework.permissions import IsAuthenticated
from django.http import Http404


if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.generics import GenericAPIView


class IsAssociatedModelOwner(BasePermission):
    def has_permission(self, request: Request, view: GenericAPIView):
        if request.method != "GET":
            return False

        benchmark_id = view.kwargs.get("benchmark_id")
        model_id = view.kwargs.get("model_id")

        try:
            model = MlCube.objects.get(pk=model_id)
        except MlCube.DoesNotExist:
            raise Http404(f'Model container with ID {model_id} does not exist!')

        is_model_owner = model.owner.id == request.user.id
        benchmark_model_association = BenchmarkModel.objects.filter(
            model_mlcube__id=model_id, benchmark__id=benchmark_id
        ).order_by('-created_at').first()
        if benchmark_model_association is None:
            return False

        benchmark_model_association_approved = (
            benchmark_model_association.approval_status == 'APPROVED'
        )

        return is_model_owner and benchmark_model_association_approved


class IsAuthenticatedAndIsPostRequest(IsAuthenticated):
    def has_permission(self, request: Request, view: GenericAPIView):
        if request.method != "POST":
            return False

        return super().has_permission(request, view)

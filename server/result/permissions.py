from rest_framework.permissions import BasePermission
from benchmark.models import Benchmark
from dataset.models import Dataset
from model.models import Model
from .models import ModelResult


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsExecutionOwner(BasePermission):
    """Whoever created the execution.

    For everything but a confidential end-to-end run this is the dataset owner,
    since they are the only one who could have created it -- so replacing the
    dataset-owner check with this one changes nothing there. Where it does
    change something is the case it exists for: an execution somebody else
    operated on a dataset they do not own."""

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


class IsConfidentialEndToEndExecution(BasePermission):
    """Anybody may create an execution a confidential VM computes end to end.

    Such a result comes back attested: which script ran, on which inputs,
    producing exactly these metrics, inside genuine confidential hardware. That
    is what makes the identity of whoever submitted it beside the point, and so
    the dataset owner no longer has to be the party holding the CLI.

    It applies to nothing else. Any other topology, or a model whose weights are
    public, still requires the dataset owner."""

    def get_benchmark(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            return None

    def get_model(self, pk):
        try:
            return Model.objects.get(pk=pk)
        except Model.DoesNotExist:
            return None

    def has_permission(self, request, view):
        if request.method != "POST":
            return False

        benchmark = self.get_benchmark(request.data.get("benchmark", None))
        model = self.get_model(request.data.get("model", None))
        if not benchmark or not model:
            return False

        if not benchmark.is_end_to_end_topology:
            return False
        return model.is_local_asset


class IsDatasetOwner(BasePermission):
    def get_result_object(self, pk):
        try:
            return ModelResult.objects.get(pk=pk)
        except ModelResult.DoesNotExist:
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
            result_pk = view.kwargs.get("pk", None)
            result = self.get_result_object(result_pk)
            if not result:
                return False
            pk = result.dataset.id
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
            return None

    def get_benchmark_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            return None

    def has_permission(self, request, view):
        if request.method == "GET":
            result_pk = view.kwargs.get("pk", None)
            result = self.get_result_object(result_pk)
            if not result:
                return False
            pk = result.benchmark.id
        if not pk:
            return False
        benchmark = self.get_benchmark_object(pk)
        if not benchmark:
            return False
        if benchmark.owner.id == request.user.id:
            return True
        else:
            return False


class IsCommitteeMember(BasePermission):
    def get_result_object(self, pk):
        try:
            return ModelResult.objects.get(pk=pk)
        except ModelResult.DoesNotExist:
            return None

    def get_benchmark_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = None
        if request.method == "GET":
            result_pk = view.kwargs.get("pk", None)
            result = self.get_result_object(result_pk)
            if not result:
                return False
            pk = result.benchmark.id
        if not pk:
            return False
        benchmark = self.get_benchmark_object(pk)
        if not benchmark:
            return False
        return benchmark.committee_members.filter(id=request.user.id).exists()

from mlcube.serializers import MlCubeSerializer
from dataset.serializers import DatasetSerializer
from result.serializers import ModelResultSerializer
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .models import Benchmark
from .serializers import BenchmarkSerializer, BenchmarkApprovalSerializer
from .permissions import IsAdmin, IsBenchmarkOwner


class BenchmarkList(GenericAPIView):
    serializer_class = BenchmarkSerializer
    queryset = ""

    def get(self, request, format=None):
        """
        List all benchmarks
        """
        benchmarks = Benchmark.objects.all()
        serializer = BenchmarkSerializer(benchmarks, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """
        Create a new benchmark
        """
        serializer = BenchmarkSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BenchmarkModelList(GenericAPIView):
    serializer_class = MlCubeSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve models associated with a benchmark instance.
        """
        benchmark = self.get_object(pk)
        modelgroups = benchmark.benchmarkmodel_set.all()
        models = [gp.model_mlcube for gp in modelgroups]
        serializer = MlCubeSerializer(models, many=True)
        return Response(serializer.data)


class BenchmarkDatasetList(GenericAPIView):
    serializer_class = DatasetSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve datasets associated with a benchmark instance.
        """
        benchmark = self.get_object(pk)
        datasetgroups = benchmark.benchmarkdataset_set.all()
        datasets = [gp.dataset for gp in datasetgroups]
        serializer = DatasetSerializer(datasets, many=True)
        return Response(serializer.data)


class BenchmarkResultList(GenericAPIView):
    permission_classes = [IsAdmin | IsBenchmarkOwner]
    serializer_class = ModelResultSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve results associated with a benchmark instance.
        """
        benchmark = self.get_object(pk)
        results = benchmark.modelresult_set.all()
        serializer = ModelResultSerializer(results, many=True)
        return Response(serializer.data)


class BenchmarkDetail(GenericAPIView):
    serializer_class = BenchmarkApprovalSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT":
            self.permission_classes = [IsAdmin | IsBenchmarkOwner]
        elif self.request.method == "DELETE":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

    #def get_serializer_class(self):
    #    if self.request.method == "PUT" or self.request.method == "DELETE":
    #        return BenchmarkApprovalSerializer
    #    return BenchmarkSerializer

    def get_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve a benchmark instance.
        """
        benchmark = self.get_object(pk)
        serializer = BenchmarkSerializer(benchmark)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a benchmark instance.
        """
        benchmark = self.get_object(pk)
        serializer = BenchmarkApprovalSerializer(benchmark, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete a benchmark instance.
        """
        benchmark = self.get_object(pk)
        benchmark.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

from benchmarkmodel.serializers import BenchmarkListofModelsSerializer
from benchmarkdataset.serializers import BenchmarkListofDatasetsSerializer
from result.serializers import ModelResultSerializer
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .models import Benchmark
from .serializers import BenchmarkSerializer, BenchmarkApprovalSerializer
from .permissions import IsAdmin, IsBenchmarkOwner, IsAssociatedDatasetOwner


class BenchmarkList(GenericAPIView):
    serializer_class = BenchmarkSerializer
    queryset = ""

    @extend_schema(operation_id="benchmarks_retrieve_all")
    def get(self, request, format=None):
        """
        List all benchmarks
        """
        benchmarks = Benchmark.objects.all()
        benchmarks = self.paginate_queryset(benchmarks)
        serializer = BenchmarkSerializer(benchmarks, many=True)
        return self.get_paginated_response(serializer.data)

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
    permission_classes = [IsAdmin | IsBenchmarkOwner | IsAssociatedDatasetOwner]
    serializer_class = BenchmarkListofModelsSerializer
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
        models = benchmark.benchmarkmodel_set.all()
        models = self.paginate_queryset(models)
        serializer = BenchmarkListofModelsSerializer(models, many=True)
        return self.get_paginated_response(serializer.data)


class BenchmarkDatasetList(GenericAPIView):
    permission_classes = [IsAdmin | IsBenchmarkOwner]
    serializer_class = BenchmarkListofDatasetsSerializer
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
        datasets = benchmark.benchmarkdataset_set.all()
        datasets = self.paginate_queryset(datasets)
        serializer = BenchmarkListofDatasetsSerializer(datasets, many=True)
        return self.get_paginated_response(serializer.data)


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
        results = self.paginate_queryset(results)
        serializer = ModelResultSerializer(results, many=True)
        return self.get_paginated_response(serializer.data)


class BenchmarkDetail(GenericAPIView):
    serializer_class = BenchmarkApprovalSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT":
            self.permission_classes = [IsAdmin | IsBenchmarkOwner]
        elif self.request.method == "DELETE":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

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
        serializer = BenchmarkApprovalSerializer(
            benchmark, data=request.data, partial=True
        )
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

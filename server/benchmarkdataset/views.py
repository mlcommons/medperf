from .models import BenchmarkDataset
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .permissions import IsAdmin, IsDatasetOwner, IsBenchmarkOwner
from .serializers import (
    BenchmarkDatasetListSerializer,
    DatasetApprovalSerializer,
)


class BenchmarkDatasetList(GenericAPIView):
    permission_classes = [IsAdmin | IsBenchmarkOwner | IsDatasetOwner]
    serializer_class = BenchmarkDatasetListSerializer
    queryset = ""

    def post(self, request, format=None):
        """
        Associate a dataset to a benchmark
        """
        serializer = BenchmarkDatasetListSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(initiated_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BenchmarkDatasetApproval(GenericAPIView):
    serializer_class = BenchmarkDatasetListSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return BenchmarkDataset.objects.filter(dataset__id=pk)
        except BenchmarkDataset.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve all benchmarks associated with a dataset
        """
        benchmarkdataset = self.get_object(pk)
        benchmarkdataset = self.paginate_queryset(benchmarkdataset)
        serializer = BenchmarkDatasetListSerializer(benchmarkdataset, many=True)
        return self.get_paginated_response(serializer.data)


class DatasetApproval(GenericAPIView):
    permission_classes = [IsAdmin | IsBenchmarkOwner | IsDatasetOwner]
    serializer_class = DatasetApprovalSerializer
    queryset = ""

    def get_object(self, dataset_id, benchmark_id):
        try:
            return BenchmarkDataset.objects.filter(
                dataset__id=dataset_id, benchmark__id=benchmark_id
            )
        except BenchmarkDataset.DoesNotExist:
            raise Http404

    def get(self, request, pk, bid, format=None):
        """
        Retrieve approval status of benchmark dataset associations
        """
        benchmarkdataset = self.get_object(pk, bid)
        serializer = DatasetApprovalSerializer(benchmarkdataset, many=True)
        return Response(serializer.data)

    def put(self, request, pk, bid, format=None):
        """
        Update approval status of the last benchmark dataset association
        """
        benchmarkdataset = self.get_object(pk, bid).order_by("-created_at").first()
        serializer = DatasetApprovalSerializer(
            benchmarkdataset, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, bid, format=None):
        """
        Delete a benchmark dataset association
        """
        benchmarkdataset = self.get_object(pk, bid)
        benchmarkdataset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

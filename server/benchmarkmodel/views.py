from .models import BenchmarkModel
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .permissions import IsAdmin, IsMlCubeOwner, IsBenchmarkOwner
from .serializers import (
    BenchmarkModelListSerializer,
    ModelApprovalSerializer,
)


class BenchmarkModelList(GenericAPIView):
    permission_classes = [IsAdmin | IsBenchmarkOwner | IsMlCubeOwner]
    serializer_class = BenchmarkModelListSerializer
    queryset = ""

    def post(self, request, format=None):
        """
        Associate a model to a benchmark
        """
        serializer = BenchmarkModelListSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(initiated_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BenchmarkModelApproval(GenericAPIView):
    serializer_class = BenchmarkModelListSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return BenchmarkModel.objects.filter(model_mlcube__id=pk)
        except BenchmarkModel.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve all benchmarks associated with a model
        """
        benchmarkmodel = self.get_object(pk)
        benchmarkmodel = self.paginate_queryset(benchmarkmodel)
        serializer = BenchmarkModelListSerializer(benchmarkmodel, many=True)
        return self.get_paginated_response(serializer.data)


class ModelApproval(GenericAPIView):
    serializer_class = ModelApprovalSerializer
    queryset = ""

    def get_permissions(self):
        self.permission_classes = [IsAdmin | IsBenchmarkOwner | IsMlCubeOwner]
        if self.request.method == "PUT" and "priority" in self.request.data:
            self.permission_classes = [IsAdmin | IsBenchmarkOwner]
        return super(self.__class__, self).get_permissions()

    def get_object(self, model_id, benchmark_id):
        try:
            return BenchmarkModel.objects.filter(
                model_mlcube__id=model_id, benchmark__id=benchmark_id
            )
        except BenchmarkModel.DoesNotExist:
            raise Http404

    def get(self, request, pk, bid, format=None):
        """
        Retrieve approval status of benchmark model associations
        """
        benchmarkmodel = self.get_object(pk, bid)
        serializer = ModelApprovalSerializer(benchmarkmodel, many=True)
        return Response(serializer.data)

    def put(self, request, pk, bid, format=None):
        """
        Update approval status of the last benchmark model association
        """
        benchmarkmodel = self.get_object(pk, bid).order_by("-created_at").first()
        serializer = ModelApprovalSerializer(
            benchmarkmodel, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, bid, format=None):
        """
        Delete benchmark model associations
        """
        benchmarkmodel = self.get_object(pk, bid)
        benchmarkmodel.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

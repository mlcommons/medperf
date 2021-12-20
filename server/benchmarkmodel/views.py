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
        serializer = BenchmarkModelListSerializer(data=request.data)
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
        serializer = BenchmarkModelListSerializer(benchmarkmodel, many=True)
        return Response(serializer.data)


class ModelApproval(GenericAPIView):
    permission_classes = [IsAdmin | IsBenchmarkOwner | IsMlCubeOwner]
    serializer_class = ModelApprovalSerializer
    queryset = ""

    def get_object(self, model_id, benchmark_id):
        try:
            return BenchmarkModel.objects.get(
                model_mlcube__id=model_id, benchmark__id=benchmark_id
            )
        except BenchmarkModel.DoesNotExist:
            raise Http404

    def get(self, request, pk, bid, format=None):
        """
        Retrieve approval status of benchmark model association
        """
        benchmarkmodel = self.get_object(pk, bid)
        serializer = ModelApprovalSerializer(benchmarkmodel)
        return Response(serializer.data)

    def put(self, request, pk, bid, format=None):
        """
        Update approval status of benchmark model association
        """
        benchmarkmodel = self.get_object(pk, bid)
        serializer = ModelApprovalSerializer(
            benchmarkmodel, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, bid, format=None):
        """
        Delete a benchmark model association
        """
        benchmarkmodel = self.get_object(pk, bid)
        benchmarkmodel.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

from user.serializers import UserSerializer, UserPasswordSerializer
from mlcube.serializers import MlCubeSerializer
from dataset.serializers import DatasetSerializer
from result.serializers import ModelResultSerializer
from benchmark.serializers import BenchmarkSerializer
from benchmarkdataset.serializers import BenchmarkDatasetListSerializer
from benchmarkmodel.serializers import BenchmarkModelListSerializer
from benchmark.models import Benchmark
from dataset.models import Dataset
from mlcube.models import MlCube
from result.models import ModelResult
from benchmarkmodel.models import BenchmarkModel
from benchmarkdataset.models import BenchmarkDataset
from django.http import Http404
from django.conf import settings
from django.db.models import Q
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers


class User(GenericAPIView):
    serializer_class = UserSerializer
    queryset = ""

    def get(self, request, format=None):
        """
        Retrieve info of the current user
        """
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)


class UserPassword(GenericAPIView):
    serializer_class = UserPasswordSerializer
    queryset = ""

    def post(self, request, format=None):
        """
        Update user credentials
        """
        serializer = UserPasswordSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            # Delete user token
            request.user.auth_token.delete()
            return Response({"message": "Password changed successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BenchmarkList(GenericAPIView):
    serializer_class = BenchmarkSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return Benchmark.objects.filter(owner__id=pk)
        except Benchmark.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all benchmarks owned by the current user
        """
        benchmarks = self.get_object(request.user.id)
        benchmarks = self.paginate_queryset(benchmarks)
        serializer = BenchmarkSerializer(benchmarks, many=True)
        return self.get_paginated_response(serializer.data)


class MlCubeList(GenericAPIView):
    serializer_class = MlCubeSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return MlCube.objects.filter(owner__id=pk)
        except MlCube.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all mlcubes associated with the current user
        """
        mlcubes = self.get_object(request.user.id)
        mlcubes = self.paginate_queryset(mlcubes)
        serializer = MlCubeSerializer(mlcubes, many=True)
        return self.get_paginated_response(serializer.data)


class DatasetList(GenericAPIView):
    serializer_class = DatasetSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return Dataset.objects.filter(owner__id=pk)
        except Dataset.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all datasets associated with the current user
        """
        datasets = self.get_object(request.user.id)
        datasets = self.paginate_queryset(datasets)
        serializer = DatasetSerializer(datasets, many=True)
        return self.get_paginated_response(serializer.data)


class ModelResultList(GenericAPIView):
    serializer_class = ModelResultSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return ModelResult.objects.filter(owner__id=pk)
        except ModelResult.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all results associated with the current user
        """
        results = self.get_object(request.user.id)
        results = self.paginate_queryset(results)
        serializer = ModelResultSerializer(results, many=True)
        return self.get_paginated_response(serializer.data)


class DatasetAssociationList(GenericAPIView):
    serializer_class = BenchmarkDatasetListSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return BenchmarkDataset.objects.filter(
                Q(dataset__owner__id=pk) | Q(benchmark__owner__id=pk)
            )
        except BenchmarkDataset.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all dataset associations involving an asset of mine
        """
        benchmarkdatasets = self.get_object(request.user.id)
        benchmarkdatasets = self.paginate_queryset(benchmarkdatasets)
        serializer = BenchmarkDatasetListSerializer(benchmarkdatasets, many=True)
        return self.get_paginated_response(serializer.data)


class MlCubeAssociationList(GenericAPIView):
    serializer_class = BenchmarkModelListSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return BenchmarkModel.objects.filter(
                Q(model_mlcube__owner__id=pk) | Q(benchmark__owner__id=pk)
            )
        except BenchmarkModel.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all mlcube associations involving an asset of mine
        """
        benchmarkmodels = self.get_object(request.user.id)
        benchmarkmodels = self.paginate_queryset(benchmarkmodels)
        serializer = BenchmarkModelListSerializer(benchmarkmodels, many=True)
        return self.get_paginated_response(serializer.data)


class ServerAPIVersion(GenericAPIView):
    permission_classes = (AllowAny,)
    queryset = ""

    @extend_schema(
        responses={
            200: inline_serializer(
                name='VersionResponse',
                fields={
                    'version': serializers.CharField(),
                }
            )
        }
    )
    def get(self, request=None, format=None):
        """
        Retrieve version of Server API
        """
        result = {"version": settings.SERVER_API_VERSION}
        return Response(result)

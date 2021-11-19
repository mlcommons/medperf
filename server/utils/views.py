from user.serializers import UserSerializer
from mlcube.serializers import MlCubeSerializer
from dataset.serializers import DatasetSerializer
from result.serializers import ModelResultSerializer
from benchmark.serializers import BenchmarkSerializer
from benchmark.models import Benchmark
from dataset.models import Dataset
from mlcube.models import MlCube
from result.models import ModelResult
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response


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
        user = self.get_object(request.user.id)
        serializer = BenchmarkSerializer(user, many=True)
        return Response(serializer.data)


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
        serializer = MlCubeSerializer(mlcubes, many=True)
        return Response(serializer.data)


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
        serializer = DatasetSerializer(datasets, many=True)
        return Response(serializer.data)


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
        serializer = ModelResultSerializer(results, many=True)
        return Response(serializer.data)

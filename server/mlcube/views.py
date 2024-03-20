from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .models import MlCube
from .serializers import MlCubeSerializer, MlCubeDetailSerializer
from .permissions import IsAdmin, IsMlCubeOwner
from dataset.serializers import DatasetFullSerializer
from dataset.models import Dataset


class MlCubeList(GenericAPIView):
    serializer_class = MlCubeSerializer
    queryset = ""

    @extend_schema(operation_id="mlcubes_retrieve_all")
    def get(self, request, format=None):
        """
        List all mlcubes
        """
        mlcubes = MlCube.objects.all()
        mlcubes = self.paginate_queryset(mlcubes)
        serializer = MlCubeSerializer(mlcubes, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        """
        Creates a new mlcube
        """
        serializer = MlCubeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MlCubeDetail(GenericAPIView):
    serializer_class = MlCubeDetailSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT":
            self.permission_classes = [IsAdmin | IsMlCubeOwner]
        elif self.request.method == "DELETE":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

    def get_object(self, pk):
        try:
            return MlCube.objects.get(pk=pk)
        except MlCube.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve a mlcube instance.
        """
        mlcube = self.get_object(pk)
        serializer = MlCubeDetailSerializer(mlcube)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a mlcube instance.
        """
        mlcube = self.get_object(pk)
        serializer = MlCubeDetailSerializer(mlcube, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete a mlcube instance.
        """
        mlcube = self.get_object(pk)
        mlcube.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MlCubeDatasetList(GenericAPIView):
    permission_classes = [IsAdmin | IsMlCubeOwner]
    serializer_class = DatasetFullSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return MlCube.objects.get(pk=pk)
        except MlCube.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve datasets associated with an MlCube instance.
        """
        mlcube = self.get_object(pk)
        if mlcube.state != "DEVELOPMENT":
            errors = {"error": "The mlcube is not in DEVELOPMENT"}
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        datasets = Dataset.objects.all().filter(data_preparation_mlcube__pk=pk)
        datasets = self.paginate_queryset(datasets)
        serializer = DatasetFullSerializer(datasets, many=True)
        return self.get_paginated_response(serializer.data)

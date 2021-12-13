from .models import Dataset
from .serializers import DatasetSerializer
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .permissions import IsAdmin, IsDatasetOwner


class DatasetList(GenericAPIView):
    serializer_class = DatasetSerializer
    queryset = ""

    def get(self, request, format=None):
        """
        List all datasets
        """
        datasets = Dataset.objects.all()
        serializer = DatasetSerializer(datasets, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """
        Creates a new dataset
        """
        serializer = DatasetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DatasetDetail(GenericAPIView):
    serializer_class = DatasetSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT":
            self.permission_classes = [IsAdmin | IsDatasetOwner]
        elif self.request.method == "DELETE":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

    def get_object(self, pk):
        try:
            return Dataset.objects.get(pk=pk)
        except Dataset.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve a dataset instance.
        """
        dataset = self.get_object(pk)
        serializer = DatasetSerializer(dataset)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a dataset instance.
        """
        dataset = self.get_object(pk)
        serializer = DatasetSerializer(dataset, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete a dataset instance.
        """
        dataset = self.get_object(pk)
        dataset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

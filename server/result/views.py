from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .models import ModelResult
from .serializers import ModelResultSerializer
from .permissions import IsAdmin, IsBenchmarkOwner, IsDatasetOwner, IsResultOwner


class ModelResultList(GenericAPIView):
    serializer_class = ModelResultSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "GET":
            self.permission_classes = [IsAdmin]
        elif self.request.method == "POST":
            self.permission_classes = [IsAdmin | IsDatasetOwner]
        return super(self.__class__, self).get_permissions()

    @extend_schema(operation_id="results_retrieve_all")
    def get(self, request, format=None):
        """
        List all results
        """
        modelresults = ModelResult.objects.all()
        modelresults = self.paginate_queryset(modelresults)
        serializer = ModelResultSerializer(modelresults, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        """
        Creates a new result
        """
        serializer = ModelResultSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModelResultDetail(GenericAPIView):
    serializer_class = ModelResultSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT" or self.request.method == "DELETE":
            self.permission_classes = [IsAdmin | IsResultOwner]
        elif self.request.method == "GET":
            self.permission_classes = [IsAdmin | IsDatasetOwner | IsBenchmarkOwner]
        return super(self.__class__, self).get_permissions()

    def get_object(self, pk):
        try:
            return ModelResult.objects.get(pk=pk)
        except ModelResult.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve a result instance.
        """
        modelresult = self.get_object(pk)
        serializer = ModelResultSerializer(modelresult)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a result instance.
        """
        modelresult = self.get_object(pk)
        serializer = ModelResultSerializer(modelresult, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete a result instance.
        """
        modelresult = self.get_object(pk)
        modelresult.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

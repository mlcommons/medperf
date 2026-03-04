from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .models import Model
from .serializers import ModelSerializer, ModelDetailSerializer
from .permissions import IsAdmin, IsModelOwner


class ModelList(GenericAPIView):
    serializer_class = ModelSerializer
    queryset = ""
    filterset_fields = ("type",)

    @extend_schema(operation_id="models_retrieve_all")
    def get(self, request, format=None):
        """
        List all models
        """
        models = Model.objects.all()
        models = self.filter_queryset(models)
        models = self.paginate_queryset(models)
        serializer = ModelSerializer(models, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        """
        Creates a new model
        """
        serializer = ModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModelDetail(GenericAPIView):
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT":
            self.permission_classes = [IsAdmin | IsModelOwner]
        elif self.request.method == "DELETE":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

    def get_object(self, pk):
        try:
            return Model.objects.get(pk=pk)
        except Model.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve a model instance.
        """
        model = self.get_object(pk)
        serializer = ModelSerializer(model)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a model instance.
        """
        model = self.get_object(pk)
        serializer = ModelDetailSerializer(model, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete a model instance.
        """
        model = self.get_object(pk)
        model.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

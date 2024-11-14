from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .models import Execution
from .serializers import ExecutionSerializer, ExecutionDetailSerializer
from .permissions import IsAdmin, IsBenchmarkOwner, IsDatasetOwner


class ExecutionList(GenericAPIView):
    serializer_class = ExecutionSerializer
    queryset = ""
    filterset_fields = ('name', 'owner', 'benchmark', 'model', 'dataset', 'is_valid', 'approval_status')

    def get_permissions(self):
        if self.request.method == "GET":
            self.permission_classes = [IsAdmin]
        elif self.request.method == "POST":
            self.permission_classes = [IsAdmin | IsDatasetOwner]
        return super(self.__class__, self).get_permissions()

    @extend_schema(operation_id="results_retrieve_all")
    def get(self, request, format=None):
        """
        List all executions
        """
        executions = Execution.objects.all()
        executions = self.filter_queryset(executions)
        executions = self.paginate_queryset(executions)
        serializer = ExecutionSerializer(executions, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        """
        Creates a new execution
        """
        serializer = ExecutionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExecutionDetail(GenericAPIView):
    serializer_class = ExecutionDetailSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT" or self.request.method == "DELETE":
            self.permission_classes = [IsAdmin]
        elif self.request.method == "GET":
            self.permission_classes = [IsAdmin | IsDatasetOwner | IsBenchmarkOwner]
        return super(self.__class__, self).get_permissions()

    def get_object(self, pk):
        try:
            return Execution.objects.get(pk=pk)
        except Execution.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve a execution instance.
        """
        Execution = self.get_object(pk)
        serializer = ExecutionDetailSerializer(Execution)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a execution instance.
        """
        Execution = self.get_object(pk)
        serializer = ExecutionDetailSerializer(Execution, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete an execution instance.
        """
        Execution = self.get_object(pk)
        Execution.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

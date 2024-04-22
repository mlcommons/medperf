from aggregator.serializers import (
    AggregatorSerializer,
)
from traindataset_association.serializers import (
    TrainingExperimentListofDatasetsSerializer,
)
from ca.serializers import CASerializer
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .models import TrainingExperiment
from .serializers import (
    WriteTrainingExperimentSerializer,
    ReadTrainingExperimentSerializer,
)
from .permissions import (
    IsAdmin,
    IsExpOwner,
    IsAssociatedDatasetOwner,
    IsAggregatorOwner,
)


class TrainingExperimentList(GenericAPIView):
    serializer_class = WriteTrainingExperimentSerializer
    queryset = ""

    @extend_schema(operation_id="training_retrieve_all")
    def get(self, request, format=None):
        """
        List all training experiments
        """
        training_exps = TrainingExperiment.objects.all()
        training_exps = self.paginate_queryset(training_exps)
        serializer = WriteTrainingExperimentSerializer(training_exps, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        """
        Create a new TrainingExperiment
        """
        serializer = WriteTrainingExperimentSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrainingAggregator(GenericAPIView):
    permission_classes = [IsAdmin | IsExpOwner | IsAssociatedDatasetOwner]
    serializer_class = AggregatorSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            training_exp = TrainingExperiment.objects.get(pk=pk)
        except TrainingExperiment.DoesNotExist:
            raise Http404

        aggregator = training_exp.aggregator
        if not aggregator:
            raise Http404
        return aggregator

    def get(self, request, pk, format=None):
        """
        Retrieve the aggregator associated with a training exp instance.
        """
        aggregator = self.get_object(pk)
        serializer = AggregatorSerializer(aggregator)
        return Response(serializer.data)


class TrainingDatasetList(GenericAPIView):
    permission_classes = [IsAdmin | IsExpOwner]
    serializer_class = TrainingExperimentListofDatasetsSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return TrainingExperiment.objects.get(pk=pk)
        except TrainingExperiment.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve datasets associated with a training experiment instance.
        """
        training_exp = self.get_object(pk)
        datasets = training_exp.traindataset_association_set.all()
        datasets = self.paginate_queryset(datasets)
        serializer = TrainingExperimentListofDatasetsSerializer(datasets, many=True)
        return self.get_paginated_response(serializer.data)


class TrainingCA(GenericAPIView):
    permission_classes = [
        IsAdmin | IsExpOwner | IsAssociatedDatasetOwner | IsAggregatorOwner
    ]
    serializer_class = CASerializer
    queryset = ""

    def get_object(self, pk):
        try:
            training_exp = TrainingExperiment.objects.get(pk=pk)
        except TrainingExperiment.DoesNotExist:
            raise Http404

        ca = training_exp.ca
        if not ca:
            raise Http404
        return ca

    def get(self, request, pk, format=None):
        """
        Retrieve CA associated with a training experiment instance.
        """
        ca = self.get_object(pk)
        serializer = CASerializer(ca)
        return Response(serializer.data)


class TrainingExperimentDetail(GenericAPIView):
    serializer_class = ReadTrainingExperimentSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT":
            self.permission_classes = [IsAdmin | IsExpOwner]
            if "approval_status" in self.request.data:
                self.permission_classes = [IsAdmin]
        elif self.request.method == "DELETE":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

    def get_object(self, pk):
        try:
            return TrainingExperiment.objects.get(pk=pk)
        except TrainingExperiment.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve a TrainingExperiment instance.
        """
        training_exp = self.get_object(pk)
        serializer = ReadTrainingExperimentSerializer(training_exp)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a TrainingExperiment instance.
        """
        training_exp = self.get_object(pk)
        serializer = ReadTrainingExperimentSerializer(
            training_exp, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete a training experiment instance.
        """
        training_exp = self.get_object(pk)
        training_exp.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

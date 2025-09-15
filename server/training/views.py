from aggregator.serializers import (
    AggregatorSerializer,
)
from traindataset_association.serializers import (
    TrainingExperimentListofDatasetsSerializer,
)
from ca.serializers import CASerializer
from trainingevent.serializers import EventDetailSerializer
from dataset.serializers import DatasetWithOwnerInfoSerializer
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from django.db.models import OuterRef, Subquery
from django.contrib.auth import get_user_model
from dataset.models import Dataset
from .models import TrainingExperiment, DatasetTrainingKit, AggregatorTrainingKit
from .serializers import (
    WriteTrainingExperimentSerializer,
    ReadTrainingExperimentSerializer,
    DatasetTrainingKitSerializer,
    AggregatorTrainingKitSerializer,
    DatasetTrainingKitListSerializer,
)
from .permissions import (
    IsAdmin,
    IsExpOwner,
    IsAssociatedDatasetOwner,
    IsAggregatorOwner,
)

User = get_user_model()


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
    permission_classes = [
        IsAdmin | IsExpOwner | IsAssociatedDatasetOwner | IsAggregatorOwner
    ]
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
        datasets = training_exp.experimentdataset_set.all()
        datasets = self.paginate_queryset(datasets)
        serializer = TrainingExperimentListofDatasetsSerializer(datasets, many=True)
        return self.get_paginated_response(serializer.data)


class TrainingCA(GenericAPIView):
    # permission_classes = [
    #     IsAdmin | IsExpOwner | IsAssociatedDatasetOwner | IsAggregatorOwner
    # ]
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


class GetTrainingEvent(GenericAPIView):
    permission_classes = [
        IsAdmin | IsExpOwner | IsAssociatedDatasetOwner | IsAggregatorOwner
    ]
    serializer_class = EventDetailSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            training_exp = TrainingExperiment.objects.get(pk=pk)
        except TrainingExperiment.DoesNotExist:
            raise Http404

        event = training_exp.event
        if not event:
            raise Http404
        return event

    def get(self, request, pk, format=None):
        """
        Retrieve latest event of a training experiment instance.
        """
        event = self.get_object(pk)
        serializer = EventDetailSerializer(event)
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


class ParticipantsInfo(GenericAPIView):
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
        latest_datasets_assocs_status = (
            training_exp.experimentdataset_set.all()
            .filter(dataset__id=OuterRef("id"))
            .order_by("-created_at")[:1]
            .values("approval_status")
        )
        datasets_with_users = (
            Dataset.objects.all()
            .annotate(assoc_status=Subquery(latest_datasets_assocs_status))
            .filter(assoc_status="APPROVED")
        )
        datasets_with_users = self.paginate_queryset(datasets_with_users)
        serializer = DatasetWithOwnerInfoSerializer(datasets_with_users, many=True)
        return self.get_paginated_response(serializer.data)


class GetTrainingKit(GenericAPIView):
    serializer_class = DatasetTrainingKitSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return TrainingExperiment.objects.get(pk=pk)
        except TrainingExperiment.DoesNotExist:
            raise Http404

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = [IsAdmin | IsExpOwner]
        return super(self.__class__, self).get_permissions()

    def post(self, request, pk, format=None):
        """
        Create a new DatasetTrainingKit
        """
        training_exp = self.get_object(pk)
        serializer = DatasetTrainingKitListSerializer(
            data=request.data, context={"experiment": training_exp}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk, format=None):
        """
        Retrieve datasets associated with a training experiment instance.
        """
        training_kit = DatasetTrainingKit.objects.filter(
            email=request.user.email, experiment__id=pk
        ).last()
        if training_kit is None:
            raise Http404

        serializer = DatasetTrainingKitSerializer(training_kit)
        return Response(serializer.data)


class GetAggregatorKit(GenericAPIView):
    serializer_class = AggregatorTrainingKitSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return TrainingExperiment.objects.get(pk=pk)
        except TrainingExperiment.DoesNotExist:
            raise Http404

    def get_permissions(self):
        if self.request.method == "POST":
            self.permission_classes = [IsAdmin | IsExpOwner]
        return super(self.__class__, self).get_permissions()

    def post(self, request, pk, format=None):
        """
        Create a new AggregatorTrainingKit
        """
        training_exp = self.get_object(pk)
        serializer = AggregatorTrainingKitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(experiment=training_exp)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk, format=None):
        """
        Retrieve datasets associated with a training experiment instance.
        """
        aggregator_kit = AggregatorTrainingKit.objects.filter(
            aggregator__owner__id=request.user.id, experiment__id=pk
        ).last()
        if aggregator_kit is None:
            raise Http404

        serializer = AggregatorTrainingKitSerializer(aggregator_kit)
        return Response(serializer.data)

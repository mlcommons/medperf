from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .models import TrainingExperiment
from .serializers import (
    WriteTrainingExperimentSerializer,
    ReadTrainingExperimentSerializer,
)
from .permissions import IsAdmin, IsExpOwner
from dataset.serializers import DatasetPublicSerializer
from aggregator.serializers import AggregatorSerializer
from drf_spectacular.utils import extend_schema
from aggregator_association.utils import latest_agg_associations
from traindataset_association.utils import latest_data_associations


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


class TrainingExperimentDetail(GenericAPIView):
    serializer_class = ReadTrainingExperimentSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT":
            self.permission_classes = [IsAdmin | IsExpOwner]
            if "approval_status" in self.request.data:
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


class TrainingDatasetList(GenericAPIView):
    serializer_class = DatasetPublicSerializer
    queryset = ""

    def get(self, request, pk, format=None):
        """
        Retrieve datasets associated with a training_exp instance.
        """
        experiment_datasets = latest_data_associations(pk)
        experiment_datasets = experiment_datasets.filter(approval_status="APPROVED")
        datasets = [exp_dset.dataset for exp_dset in experiment_datasets]
        datasets = self.paginate_queryset(datasets)
        serializer = DatasetPublicSerializer(datasets, many=True)
        return self.get_paginated_response(serializer.data)


class GetAggregator(GenericAPIView):
    serializer_class = AggregatorSerializer
    queryset = ""

    def get(self, request, pk, format=None):
        """
        Retrieve aggregator associated with a training exp instance.
        """
        experiment_aggregators = latest_agg_associations(pk)
        experiment_aggregators = experiment_aggregators.filter(
            approval_status="APPROVED"
        )
        aggregators = [exp_agg.aggregator for exp_agg in experiment_aggregators]
        if aggregators:
            serializer = AggregatorSerializer(aggregators[0])
            return Response(serializer.data)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

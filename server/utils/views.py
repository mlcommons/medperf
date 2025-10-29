from user.serializers import UserSerializer
from mlcube.serializers import MlCubeSerializer
from dataset.serializers import DatasetFullSerializer
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
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from training.models import TrainingExperiment
from training.serializers import ReadTrainingExperimentSerializer
from aggregator.models import Aggregator
from aggregator.serializers import AggregatorSerializer
from traindataset_association.models import ExperimentDataset
from traindataset_association.serializers import ExperimentDatasetListSerializer
from aggregator_association.models import ExperimentAggregator
from aggregator_association.serializers import ExperimentAggregatorListSerializer
from ca_association.models import ExperimentCA
from ca_association.serializers import ExperimentCAListSerializer
from trainingevent.serializers import EventDetailSerializer
from ca.serializers import CASerializer
from trainingevent.models import TrainingEvent
from ca.models import CA
from certificate.models import Certificate
from certificate.serializers import CertificateDetailSerializer
from mlcube_key.models import MlCubeKey
from mlcube_key.serializers import EncryptedKeyDetailSerializer


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
        benchmarks = self.get_object(request.user.id)
        benchmarks = self.paginate_queryset(benchmarks)
        serializer = BenchmarkSerializer(benchmarks, many=True)
        return self.get_paginated_response(serializer.data)


class TrainingExperimentList(GenericAPIView):
    serializer_class = ReadTrainingExperimentSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return TrainingExperiment.objects.filter(owner__id=pk)
        except TrainingExperiment.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all training_exps owned by the current user
        """
        training_exps = self.get_object(request.user.id)
        training_exps = self.paginate_queryset(training_exps)
        serializer = ReadTrainingExperimentSerializer(training_exps, many=True)
        return self.get_paginated_response(serializer.data)


class TrainingEventList(GenericAPIView):
    serializer_class = EventDetailSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return TrainingEvent.objects.filter(owner__id=pk)
        except TrainingEvent.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all events owned by the current user
        """
        training_events = self.get_object(request.user.id)
        training_events = self.paginate_queryset(training_events)
        serializer = EventDetailSerializer(training_events, many=True)
        return self.get_paginated_response(serializer.data)


class AggregatorList(GenericAPIView):
    serializer_class = AggregatorSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return Aggregator.objects.filter(owner__id=pk)
        except Aggregator.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all aggregators owned by the current user
        """
        aggregators = self.get_object(request.user.id)
        aggregators = self.paginate_queryset(aggregators)
        serializer = AggregatorSerializer(aggregators, many=True)
        return self.get_paginated_response(serializer.data)


class CAList(GenericAPIView):
    serializer_class = CASerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return CA.objects.filter(owner__id=pk)
        except CA.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all CAs owned by the current user
        """
        cas = self.get_object(request.user.id)
        cas = self.paginate_queryset(cas)
        serializer = CASerializer(cas, many=True)
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
    serializer_class = DatasetFullSerializer
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
        serializer = DatasetFullSerializer(datasets, many=True)
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


class CertificateList(GenericAPIView):
    serializer_class = CertificateDetailSerializer
    queryset = ""
    filterset_fields = ("name", "owner", "is_valid", "ca")

    def get_object(self, pk):
        try:
            return Certificate.objects.filter(owner__id=pk)
        except Certificate.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all certs associated with the current user
        """
        certs = self.get_object(request.user.id)
        certs = self.filter_queryset(certs)
        certs = self.paginate_queryset(certs)
        serializer = CertificateDetailSerializer(certs, many=True)
        return self.get_paginated_response(serializer.data)


class MlCubeKeyList(GenericAPIView):
    serializer_class = EncryptedKeyDetailSerializer
    queryset = ""
    filterset_fields = ("name", "owner", "is_valid", "certificate", "container")

    def get_object(self, pk):
        try:
            return MlCubeKey.objects.filter(owner__id=pk)
        except MlCubeKey.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all keys associated with the current user
        """
        keys = self.get_object(request.user.id)
        keys = self.filter_queryset(keys)
        keys = self.paginate_queryset(keys)
        serializer = EncryptedKeyDetailSerializer(keys, many=True)
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


class DatasetTrainingAssociationList(GenericAPIView):
    serializer_class = ExperimentDatasetListSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            # TODO: this retrieves everything (not just latest ones)
            return ExperimentDataset.objects.filter(
                Q(dataset__owner__id=pk) | Q(training_exp__owner__id=pk)
            )
        except ExperimentDataset.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all training dataset associations involving an asset of mine
        """
        experiment_datasets = self.get_object(request.user.id)
        experiment_datasets = self.paginate_queryset(experiment_datasets)
        serializer = ExperimentDatasetListSerializer(experiment_datasets, many=True)
        return self.get_paginated_response(serializer.data)


class AggregatorAssociationList(GenericAPIView):
    serializer_class = ExperimentAggregatorListSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return ExperimentAggregator.objects.filter(
                Q(aggregator__owner__id=pk) | Q(training_exp__owner__id=pk)
            )
        except ExperimentAggregator.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all aggregator associations involving an asset of mine
        """
        experiment_aggs = self.get_object(request.user.id)
        experiment_aggs = self.paginate_queryset(experiment_aggs)
        serializer = ExperimentAggregatorListSerializer(experiment_aggs, many=True)
        return self.get_paginated_response(serializer.data)


class CAAssociationList(GenericAPIView):
    serializer_class = ExperimentCAListSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return ExperimentCA.objects.filter(
                Q(ca__owner__id=pk) | Q(training_exp__owner__id=pk)
            )
        except ExperimentCA.DoesNotExist:
            raise Http404

    def get(self, request, format=None):
        """
        Retrieve all ca associations involving an asset of mine
        """
        experiment_cas = self.get_object(request.user.id)
        experiment_cas = self.paginate_queryset(experiment_cas)
        serializer = ExperimentCAListSerializer(experiment_cas, many=True)
        return self.get_paginated_response(serializer.data)


class ServerAPIVersion(GenericAPIView):
    permission_classes = (AllowAny,)
    queryset = ""

    @extend_schema(
        responses={
            200: inline_serializer(
                name="VersionResponse",
                fields={
                    "version": serializers.CharField(),
                },
            )
        }
    )
    def get(self, request=None, format=None):
        """
        Retrieve version of Server API
        """
        result = {"version": settings.SERVER_API_VERSION}
        return Response(result)

from .models import ExperimentDataset
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .permissions import IsAdmin, IsDatasetOwner, IsExpOwner
from .serializers import (
    ExperimentDatasetListSerializer,
    DatasetApprovalSerializer,
)


class ExperimentDatasetList(GenericAPIView):
    permission_classes = [IsAdmin | IsDatasetOwner]
    serializer_class = ExperimentDatasetListSerializer
    queryset = ""

    def post(self, request, format=None):
        """
        Associate a dataset to a training_exp
        """
        serializer = ExperimentDatasetListSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(initiated_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DatasetExperimentList(GenericAPIView):
    serializer_class = ExperimentDatasetListSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return ExperimentDataset.objects.filter(dataset__id=pk)
        except ExperimentDataset.DoesNotExist:
            raise Http404

    @extend_schema(operation_id="datasets_experiments_retrieve_all")
    def get(self, request, pk, format=None):
        """
        Retrieve all experiments associated with a dataset
        """
        training_expdataset = self.get_object(pk)
        training_expdataset = self.paginate_queryset(training_expdataset)
        serializer = ExperimentDatasetListSerializer(training_expdataset, many=True)
        return self.get_paginated_response(serializer.data)


class DatasetApproval(GenericAPIView):
    serializer_class = DatasetApprovalSerializer
    queryset = ""

    def get_permissions(self):
        self.permission_classes = [IsAdmin | IsExpOwner | IsDatasetOwner]
        if self.request.method == "DELETE":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

    def get_object(self, dataset_id, training_exp_id):
        try:
            return ExperimentDataset.objects.filter(
                dataset__id=dataset_id, training_exp__id=training_exp_id
            )
        except ExperimentDataset.DoesNotExist:
            raise Http404

    def get(self, request, pk, tid, format=None):
        """
        Retrieve approval status of training_exp dataset associations
        """
        training_expdataset = self.get_object(pk, tid)
        serializer = DatasetApprovalSerializer(training_expdataset, many=True)
        return Response(serializer.data)

    def put(self, request, pk, tid, format=None):
        """
        Update approval status of the last training_exp dataset association
        """
        training_expdataset = self.get_object(pk, tid).order_by("-created_at").first()
        serializer = DatasetApprovalSerializer(
            training_expdataset, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, tid, format=None):
        """
        Delete a training_exp dataset association
        """
        training_expdataset = self.get_object(pk, tid)
        training_expdataset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

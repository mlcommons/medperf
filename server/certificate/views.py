from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Certificate
from .serializers import CertificateSerializer
from .permissions import IsModelApprovedInBenchmark, IsModelOwner
from user.permissions import IsAdmin
from drf_spectacular.utils import extend_schema
from benchmarkdataset.models import BenchmarkDataset
from dataset.models import Dataset
from user.permissions import IsOwnUser


class CertificateList(GenericAPIView):
    serializer_class = CertificateSerializer
    queryset = ""

    def get_permissions(self):
        """
        Anyone can post, but only admins can view and edit.
        Owners can get their own certificates via the CertificateDetail view
        ModelOwners can get relevant certificates via the CertificatesFromBenchmark view
        """
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        else:
            return [IsAdmin()]

    @extend_schema(operation_id="certificates_retrieve_all")
    def get(self, request, format=None):
        """
        List all certificates
        """
        certificates = Certificate.objects.all()
        certificates = self.paginate_queryset(certificates)
        serializer = CertificateSerializer(certificates, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        """
        Create a new certificate obj
        """
        serializer = CertificateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CertificateDetail(GenericAPIView):
    serializer_class = CertificateSerializer
    queryset = ""
    permission_classes = [IsAdmin | IsOwnUser]

    def get_object(self, pk):
        try:
            return Certificate.objects.get(pk=pk)
        except Certificate.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve an ca instance.
        """
        certificate = self.get_object(pk)
        serializer = CertificateSerializer(certificate)
        return Response(serializer.data)


class CertificatesFromBenchmark(GenericAPIView):
    permission_classes = [IsAdmin | (IsModelApprovedInBenchmark & IsModelOwner)]

    def get(self, request, benchmark_id, model_id, ca_id, format=None):
        benchmark_dataset_associations = BenchmarkDataset.objects.filter(
            benchmark__id=benchmark_id
        ).prefetch_related("dataset")

        dataset_ids = [
            association.dataset.id for association in benchmark_dataset_associations
        ]
        datasets = Dataset.objects.filter(pk__in=dataset_ids)
        dataset_owners = datasets.values_list("owner", flat=True)

        valid_certificates = Certificate.objects.filter(
            ca_id__id=ca_id, owner__in=dataset_owners
        )
        valid_certificates = self.paginate_queryset(valid_certificates)
        serializer = CertificateSerializer(valid_certificates, many=True)
        return self.get_paginated_response(serializer.data)

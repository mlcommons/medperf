from __future__ import annotations
from typing import TYPE_CHECKING
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Certificate
from .serializers import (
    CertificateSerializer,
    CertificateDetailSerializer,
    CertificateWithOwnerInfoSerializer,
)
from .permissions import IsAssociatedModelOwner, IsCertificateOwner, IsAdmin
from drf_spectacular.utils import extend_schema
from dataset.models import Dataset
from benchmark.models import Benchmark
from django.db.models import OuterRef, Subquery
from encrypted_key.serializers import EncryptedKeySerializer
from encrypted_key.models import EncryptedKey

if TYPE_CHECKING:
    from rest_framework.request import Request


User = get_user_model()


class CertificateList(GenericAPIView):
    serializer_class = CertificateSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "GET":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

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
    serializer_class = CertificateDetailSerializer
    queryset = ""
    permission_classes = [IsAdmin | IsCertificateOwner]

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
        serializer = CertificateDetailSerializer(certificate)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a certificate
        """
        certificate = self.get_object(pk)
        serializer = CertificateDetailSerializer(
            certificate, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CertificatesFromBenchmark(GenericAPIView):
    permission_classes = [IsAdmin | IsAssociatedModelOwner]

    def get_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            raise Http404

    def get(self, request: Request, pk: int, format=None):
        # benchmark -> latest approved dataset associations -> datasets -> owners -> certificates
        benchmark = self.get_object(pk)

        latest_datasets_assocs_status = (
            benchmark.benchmarkdataset_set.all()
            .filter(dataset__id=OuterRef("id"))
            .order_by("-created_at")[:1]
            .values("approval_status")
        )
        datasets = (
            Dataset.objects.all()
            .annotate(assoc_status=Subquery(latest_datasets_assocs_status))
            .filter(assoc_status="APPROVED")
        )
        owners_ids = datasets.values_list("owner", flat=True).distinct()
        certificates = Certificate.objects.filter(
            owner__id__in=owners_ids, is_valid=True
        )

        certificates = self.paginate_queryset(certificates)
        serializer = CertificateWithOwnerInfoSerializer(certificates, many=True)

        return self.get_paginated_response(serializer.data)


class CertificateEncryptedKeys(GenericAPIView):
    serializer_class = EncryptedKeySerializer
    queryset = ""
    filterset_fields = ("name", "owner", "is_valid", "certificate", "container")
    permission_classes = [IsAdmin | IsCertificateOwner]

    def get_object(self, pk):
        try:
            return Certificate.objects.get(pk=pk)
        except EncryptedKey.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve all keys associated with a certificate
        """
        certificate = self.get_object(pk)
        keys = certificate.encryptedkey_set.all()
        keys = self.filter_queryset(keys)
        keys = self.paginate_queryset(keys)
        serializer = EncryptedKeySerializer(keys, many=True)
        return self.get_paginated_response(serializer.data)

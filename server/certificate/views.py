from __future__ import annotations
from typing import TYPE_CHECKING
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Certificate
from .serializers import CertificateSerializer
from .permissions import IsAuthenticatedAndIsPostRequest, IsAssociatedModelOwner
from user.permissions import IsAdmin
from drf_spectacular.utils import extend_schema
from dataset.models import Dataset
from user.permissions import IsOwnUser
from mlcube_ca_encrypted_key.models import ModelCAEncryptedKey


if TYPE_CHECKING:
    from rest_framework.request import Request


User = get_user_model()


class CertificateList(GenericAPIView):
    serializer_class = CertificateSerializer
    queryset = ""
    permission_classes = [IsAdmin | IsAuthenticatedAndIsPostRequest]

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
    permission_classes = [IsAdmin | IsAssociatedModelOwner | IsOwnUser]

    def get(self, request: Request, benchmark_id: int,
            model_id: int, ca_id:int, format=None):

        already_registered_keys = ModelCAEncryptedKey.objects.filter(
            owner=request.user.id, ca_association__model_mlcube=model_id,
            ca_association__associated_ca=ca_id
        )

        data_owners_that_already_have_keys = already_registered_keys.values_list('data_owner', flat=True)
        print(f'{data_owners_that_already_have_keys=}')

        datasets_whose_owners_need_keys = Dataset.objects.exclude(
            owner__in=data_owners_that_already_have_keys
        ).filter(
            benchmarkdataset__benchmark_id=benchmark_id,
            benchmarkdataset__approval_status='APPROVED'
        )

        data_owners_that_need_keys = datasets_whose_owners_need_keys.values_list('owner', flat=True)

        required_certificates = Certificate.objects.filter(
            ca_id__id=ca_id, owner__in=data_owners_that_need_keys
        )

        required_certificates = self.paginate_queryset(required_certificates)
        serializer = CertificateSerializer(required_certificates, many=True)
        return self.get_paginated_response(serializer.data)

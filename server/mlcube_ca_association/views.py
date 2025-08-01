from django.shortcuts import render

from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .models import ContainerCA
from .serializers import ContainerCASerializer
from drf_spectacular.utils import extend_schema


class ContainerCAList(GenericAPIView):
    serializer_class = ContainerCASerializer

    @extend_schema(operation_id="mlcube_cas_retrieve_all")
    def get(self, request, format=None):
        """
        List all certificates
        """
        certificates = ContainerCA.objects.all()
        certificates = self.paginate_queryset(certificates)
        serializer = ContainerCASerializer(certificates, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, pk, format=None):
        """
        Create a new certificate obj
        """
        serializer = ContainerCASerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CertificateDetail(GenericAPIView):
    serializer_class = ContainerCASerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return ContainerCA.objects.get(pk=pk)
        except ContainerCA.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve an ca instance.
        """
        certificate = self.get_object(pk)
        serializer = ContainerCASerializer(certificate)
        return Response(serializer.data)

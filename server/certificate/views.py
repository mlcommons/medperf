from django.shortcuts import render

from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .models import Certificate
from .serializers import CertificateSerializer
from drf_spectacular.utils import extend_schema


class CertificateList(GenericAPIView):
    serializer_class = CertificateSerializer
    queryset = ""

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

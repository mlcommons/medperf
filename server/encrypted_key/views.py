from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .models import EncryptedKey
from .serializers import (
    EncryptedKeySerializer,
    CreateEncryptedKeyListSerializer,
    UpdateEncryptedKeyListSerializer,
)
from .permissions import IsAdmin, IsKeyOwnerForGet, IsKeyOwnerForPut, IsContainerOwner
from rest_framework.request import Request
from django.contrib.auth import get_user_model
from django.http import Http404

User = get_user_model()


class GetEncryptedKeyById(GenericAPIView):
    serializer_class = EncryptedKeySerializer
    queryset = ""
    permission_classes = [IsAdmin | IsKeyOwnerForGet]

    def get_object(self, pk):
        try:
            return EncryptedKey.objects.get(pk=pk)
        except EncryptedKey.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        encrypted_key = self.get_object(pk)
        serializer = EncryptedKeySerializer(encrypted_key)
        return Response(serializer.data)


class GetAllEncryptedKeys(GenericAPIView):
    serializer_class = EncryptedKeySerializer
    queryset = ""
    permission_classes = [IsAdmin]

    def get(self, request, format=None):
        encrypted_keys = EncryptedKey.objects.all()
        encrypted_keys = self.paginate_queryset(encrypted_keys)
        serializer = EncryptedKeySerializer(encrypted_keys, many=True)
        return self.get_paginated_response(serializer.data)


class MultipleEncryptedKeys(GenericAPIView):
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT":
            self.permission_classes = [IsAdmin | IsKeyOwnerForPut]
        elif self.request.method == "POST":
            self.permission_classes = [IsAdmin | IsContainerOwner]
        return super(self.__class__, self).get_permissions()

    def get_objects(self, pk_list):
        return EncryptedKey.objects.filter(pk__in=pk_list)

    def post(self, request: Request, format=None):
        """
        Create many encrypted key objects.
        """
        serializer = CreateEncryptedKeyListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request: Request, format=None):
        """
        update many encrypted key objects.
        """
        try:
            pk_list = [entry["id"] for entry in request.data]
        except KeyError:
            return Response("Missing 'id' field", status=status.HTTP_400_BAD_REQUEST)

        instances = self.get_objects(pk_list)
        serializer = UpdateEncryptedKeyListSerializer(
            instances, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

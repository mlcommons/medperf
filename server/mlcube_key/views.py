from rest_framework.generics import RetrieveAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework import status

from .models import MlCubeKey
from .serializers import EncryptedKeySerializer, EncryptedKeyDetailSerializer
from .permissions import IsAdmin, IsKeyOwner, IsContainersOwner
from rest_framework.request import Request
from django.contrib.auth import get_user_model
from django.http import Http404

User = get_user_model()


class GetEncryptedKeyById(RetrieveAPIView):
    serializer_class = EncryptedKeyDetailSerializer
    queryset = ""
    permission_classes = [IsAdmin | IsKeyOwner]

    def get_object(self, pk):
        try:
            return MlCubeKey.objects.get(pk=pk)
        except MlCubeKey.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        encrypted_key = self.get_object(pk)
        serializer = EncryptedKeyDetailSerializer(encrypted_key)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a key
        """
        encrypted_key = self.get_object(pk)
        serializer = EncryptedKeyDetailSerializer(
            encrypted_key, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetAllEncryptedKeys(RetrieveAPIView):
    serializer_class = EncryptedKeySerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "GET":
            self.permission_classes = [IsAdmin]
        elif self.request.method == "POST":
            self.permission_classes = [IsAdmin | IsContainersOwner]
        return super(self.__class__, self).get_permissions()

    def get(self, request, format=None):
        encrypted_keys = MlCubeKey.objects.all()
        encrypted_keys = self.paginate_queryset(encrypted_keys)
        serializer = EncryptedKeySerializer(encrypted_keys, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request: Request, format=None):
        """
        Create an encrypted key object.
        """
        serializer = EncryptedKeySerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostMultipleEncryptedKeys(CreateAPIView):
    permission_classes = [IsAdmin | IsContainersOwner]

    def post(self, request: Request, format=None):
        """
        Create many encrypted key objects.
        """
        serializer = EncryptedKeySerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

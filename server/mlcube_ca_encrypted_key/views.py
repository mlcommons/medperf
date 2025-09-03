from rest_framework.generics import RetrieveAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework import status

from .models import ModelCAEncryptedKey
from .serializers import EncryptedKeySerializer
from user.permissions import IsAdmin, IsOwnUser
from .permissions import IsDataOwnerForGet, IsModelOwnerForPost
from rest_framework.request import Request
from django.contrib.auth import get_user_model
from ca.models import CA
from ca.serializers import CASerializer
from django.http import Http404

User = get_user_model()


class GetEncryptedKeyById(RetrieveAPIView):
    serializer_class = EncryptedKeySerializer
    queryset = ""
    permission_classes = [IsAdmin | IsOwnUser]

    def get(self, request, pk, format=None):
        encrypted_key = ModelCAEncryptedKey.objects.get(pk=pk)
        serializer = EncryptedKeySerializer(encrypted_key)
        return Response(serializer.data)


class GetAllEncryptedKeys(RetrieveAPIView):
    serializer_class = EncryptedKeySerializer
    queryset = ""
    permission_classes = [IsAdmin]

    def get(self, request, format=None):
        encrypted_keys = ModelCAEncryptedKey.objects.all()
        encrypted_keys = self.paginate_queryset(encrypted_keys)
        serializer = EncryptedKeySerializer(encrypted_keys, many=True)
        return self.get_paginated_response(serializer.data)


class GetEncryptedKeyFromModelAndCA(RetrieveAPIView):
    serializer_class = EncryptedKeySerializer
    queryset = ""
    permission_classes = [IsAdmin | IsDataOwnerForGet | IsModelOwnerForPost]

    def get(self, request: Request, model_id: int, ca_id: int, format=None):
        """
        Retrieve a Key Instance
        """
        try:
            key = ModelCAEncryptedKey.objects.get(
                certificate__owner=request.user, model_container=model_id,
                certificate__ca=ca_id
            )
        except ModelCAEncryptedKey.DoesNotExist:
            return Response(
                {
                    "detail": f"The access Key to Container ID {model_id}, "
                    f"CA ID {ca_id} has not been submitted yet for "
                    f"your user({request.user.email})."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EncryptedKeySerializer(key)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetEncryptedKeyFromModel(RetrieveAPIView):
    serializer_class = EncryptedKeySerializer
    queryset = ""
    permission_classes = [IsAdmin | IsDataOwnerForGet]

    def get(self, request: Request, model_id: int, format=None):
        """
        Retrieve a Key Instance
        """

        try:
            key = ModelCAEncryptedKey.objects.get(
                certificate__owner=request.user,
                model_container=model_id
            )
        except ModelCAEncryptedKey.DoesNotExist:
            return Response(
                {
                    "detail": f"The access Key to Container ID {model_id}, "
                    f"has not been submitted yet for your user ({request.user.email})."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EncryptedKeySerializer(key)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostMultipleEncryptedKeys(CreateAPIView):
    def post(self, request: Request, format=None):
        """
        Create many encrypted key objects.
        """
        serializer = EncryptedKeySerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetCAFromEncryptedKey(RetrieveAPIView):
    serializer_class = CASerializer

    def get(self, request: Request, key_id: int, format=None):
        try:
            ca = CA.objects.get(
                certificate__modelcaencryptedkey=key_id,
                certificate__owner=request.user.id,
            )
        except CA.DoesNotExist:
            raise Http404('No CA associated with this EncryptedKey and Model for the current user.')

        ca = CASerializer(ca)
        return Response(ca.data)

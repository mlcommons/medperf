from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status

from .models import ModelCAEncryptedKey
from .serializers import EncryptedKeySerializer
from mlcube_ca_association.models import ContainerCA
from user.permissions import IsAdmin, IsOwnUser
from .permissions import IsDataOwnerForGet, IsModelOwnerForPost
from rest_framework.request import Request
from django.contrib.auth import get_user_model

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


class GetAndPostEncryptedKeyFromModelAndCA(RetrieveAPIView):
    serializer_class = EncryptedKeySerializer
    queryset = ""
    permission_classes = [IsAdmin | IsDataOwnerForGet | IsModelOwnerForPost]

    def get(self, request: Request, model_id: int, ca_id: int, format=None):
        """
        Retrieve a Key Instance
        """
        ca_association: ContainerCA = ContainerCA.get_by_model_id_and_ca_id(
            model_id=model_id, ca_id=ca_id
        )

        try:
            key = ModelCAEncryptedKey.objects.get(
                data_owner=request.user, ca_association=ca_association
            )
        except ModelCAEncryptedKey.DoesNotExist:
            return Response(
                {
                    "detail": f"The access Key to Container ID {model_id}, "
                    "CA ID {ca_id} has not been submitted yet for "
                    "your user({request.user.email})."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EncryptedKeySerializer(key)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request: Request, model_id, ca_id, format=None):
        """
        Create many encrypted key objects
        """
        model_ca_association = ContainerCA.get_by_model_id_and_ca_id(
            model_id=model_id, ca_id=ca_id
        )
        for item in request.data:
            item["ca_association"] = model_ca_association.id
            item["data_owner"] = User.objects.get(pk=item["data_owner"]).id

        serializer = EncryptedKeySerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetEncryptedKeyFromModel(RetrieveAPIView):
    serializer_class = EncryptedKeySerializer
    queryset = ""
    permission_classes = [IsAdmin | IsDataOwnerForGet]

    def get(self, request: Request, model_id: int, format=None):
        """
        Retrieve a Key Instance
        """
        ca_association: ContainerCA = ContainerCA.get_by_model_id(model_id=model_id)

        try:
            key = ModelCAEncryptedKey.objects.get(
                data_owner=request.user, ca_association=ca_association
            )
        except ModelCAEncryptedKey.DoesNotExist:
            return Response(
                {
                    "detail": f"The access Key to Container ID {model_id}, "
                    "CA ID {ca_id} has not been submitted yet for "
                    "your user({request.user.email})."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EncryptedKeySerializer(key)
        return Response(serializer.data, status=status.HTTP_200_OK)

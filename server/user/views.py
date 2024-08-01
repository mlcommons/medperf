from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema

from .serializers import UserSerializer
from .permissions import IsAdmin, IsOwnUser, IsOwnerOfUsedMLCube

User = get_user_model()


class UserList(GenericAPIView):
    permission_classes = [IsAdmin]
    serializer_class = UserSerializer
    queryset = ""

    @extend_schema(operation_id="users_retrieve_all")
    def get(self, request, format=None):
        """
        List all users
        """
        users = User.objects.all()
        users = self.paginate_queryset(users)
        serializer = UserSerializer(users, many=True)
        return self.get_paginated_response(serializer.data)


class UserDetail(GenericAPIView):
    serializer_class = UserSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "GET":
            self.permission_classes = [IsAdmin | IsOwnUser | IsOwnerOfUsedMLCube]
        elif self.request.method == "DELETE" or self.request.method == "PUT":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve a user instance.
        """
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a user instance.
        """
        user = self.get_object(pk)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete a user instance.
        """
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

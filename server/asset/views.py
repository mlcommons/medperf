from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .models import Asset
from .serializers import AssetSerializer, AssetDetailSerializer
from .permissions import IsAdmin, IsAssetOwner


class AssetList(GenericAPIView):
    serializer_class = AssetSerializer
    queryset = ""
    filterset_fields = ("name", "owner", "state", "is_valid")

    @extend_schema(operation_id="assets_retrieve_all")
    def get(self, request, format=None):
        """
        List all assets
        """
        assets = Asset.objects.all()
        assets = self.filter_queryset(assets)
        assets = self.paginate_queryset(assets)
        serializer = AssetSerializer(assets, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        """
        Creates a new asset
        """
        serializer = AssetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssetDetail(GenericAPIView):
    serializer_class = AssetDetailSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT":
            self.permission_classes = [IsAdmin | IsAssetOwner]
        elif self.request.method == "DELETE":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

    def get_object(self, pk):
        try:
            return Asset.objects.get(pk=pk)
        except Asset.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve an asset instance.
        """
        asset = self.get_object(pk)
        serializer = AssetDetailSerializer(asset)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update an asset instance.
        """
        asset = self.get_object(pk)
        serializer = AssetDetailSerializer(asset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete an asset instance.
        """
        asset = self.get_object(pk)
        asset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

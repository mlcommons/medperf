from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .models import ContainerCA
from .serializers import ContainerCASerializer
from drf_spectacular.utils import extend_schema
from ca.serializers import CASerializer


class ContainerCAList(GenericAPIView):
    serializer_class = ContainerCASerializer

    @extend_schema(operation_id="mlcube_get_associated_ca")
    def get(self, request, pk, format=None):
        """
        Get the CA associated with a Model Container
        If multiple CAs are associated, returns the most recent one (similar do training experiments)
        """
        association = (
            ContainerCA.objects.filter(model_mlcube__id=pk)
            .order_by("created_at")
            .last()
        )

        if association is None:
            return Response(
                {
                    "detail": f"No CA association was found for the given Container ID ({pk}). Please verify the Container ID."
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        ca = association.associated_ca

        serialized_ca = CASerializer(ca)
        return Response(serialized_ca.data)

    def post(self, request, pk, format=None):
        """
        Create a new Model <-> CA association object
        """
        serializer = ContainerCASerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContainerCADetail(GenericAPIView):
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

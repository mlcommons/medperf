from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .models import KBS
from .serializers import KBSSerializer
from drf_spectacular.utils import extend_schema


class KBSList(GenericAPIView):
    serializer_class = KBSSerializer
    queryset = ""

    @extend_schema(operation_id="kbss_retrieve_all")
    def get(self, request, format=None):
        """
        List all kbss
        """
        kbss = KBS.objects.all()
        kbss = self.paginate_queryset(kbss)
        serializer = KBSSerializer(kbss, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        """
        Create a new KBS
        """
        serializer = KBSSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KBSDetail(GenericAPIView):
    serializer_class = KBSSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return KBS.objects.get(pk=pk)
        except KBS.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve an kbs instance.
        """
        kbs = self.get_object(pk)
        serializer = KBSSerializer(kbs)
        return Response(serializer.data)

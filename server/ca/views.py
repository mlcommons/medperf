from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from .models import CA
from .serializers import CASerializer
from drf_spectacular.utils import extend_schema


class CAList(GenericAPIView):
    serializer_class = CASerializer
    queryset = ""

    @extend_schema(operation_id="cas_retrieve_all")
    def get(self, request: Request, format=None):
        """
        List all cas
        """
        ids_list = request.GET.getlist('ids')
        print(f'{ids_list=}')
        print(f'{request.GET=}')
        if ids_list:
            cas = CA.objects.filter(pk__in=ids_list)
        else:
            cas = CA.objects.all()
        cas = self.paginate_queryset(cas)
        serializer = CASerializer(cas, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        """
        Create a new CA
        """
        serializer = CASerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CADetail(GenericAPIView):
    serializer_class = CASerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return CA.objects.get(pk=pk)
        except CA.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve an ca instance.
        """
        ca = self.get_object(pk)
        serializer = CASerializer(ca)
        return Response(serializer.data)

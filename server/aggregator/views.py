from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .models import Aggregator
from .serializers import AggregatorSerializer
from drf_spectacular.utils import extend_schema


class AggregatorList(GenericAPIView):
    serializer_class = AggregatorSerializer
    queryset = ""

    @extend_schema(operation_id="aggregators_retrieve_all")
    def get(self, request, format=None):
        """
        List all aggregators
        """
        aggregators = Aggregator.objects.all()
        aggregators = self.paginate_queryset(aggregators)
        serializer = AggregatorSerializer(aggregators, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        """
        Create a new Aggregator
        """
        serializer = AggregatorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AggregatorDetail(GenericAPIView):
    serializer_class = AggregatorSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return Aggregator.objects.get(pk=pk)
        except Aggregator.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve an aggregator instance.
        """
        aggregator = self.get_object(pk)
        serializer = AggregatorSerializer(aggregator)
        return Response(serializer.data)

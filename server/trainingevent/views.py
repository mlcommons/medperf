from .models import TrainingEvent
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .permissions import IsAdmin, IsExpOwner, IsAggregatorOwner
from .serializers import EventSerializer, EventDetailSerializer


class EventList(GenericAPIView):
    permission_classes = [IsAdmin | IsExpOwner]
    serializer_class = EventSerializer
    queryset = ""

    def post(self, request, format=None):
        """
        Create an event for an experiment
        """
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, format=None):
        """
        get all events
        """
        events = TrainingEvent.objects.all()
        events = self.paginate_queryset(events)
        serializer = EventSerializer(events, many=True)
        return self.get_paginated_response(serializer.data)


class EventDetail(GenericAPIView):
    serializer_class = EventDetailSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT":
            self.permission_classes = [IsAdmin | IsExpOwner | IsAggregatorOwner]
        return super(self.__class__, self).get_permissions()

    def get_object(self, pk):
        try:
            return TrainingEvent.objects.get(pk=pk)
        except TrainingEvent.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve an event
        """
        event = self.get_object(pk)
        serializer = EventDetailSerializer(event)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update an event
        """
        event = self.get_object(pk)
        serializer = EventDetailSerializer(event, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

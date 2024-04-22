from training.models import TrainingExperiment
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
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventDetail(GenericAPIView):
    serializer_class = EventDetailSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT":
            self.permission_classes = [IsAdmin | IsExpOwner | IsAggregatorOwner]
        return super(self.__class__, self).get_permissions()

    def get_object(self, tid):
        try:
            training_exp = TrainingExperiment.objects.get(pk=tid)
        except TrainingExperiment.DoesNotExist:
            raise Http404

        event = training_exp.event
        if not event:
            raise Http404
        return event

    def get(self, request, tid, format=None):
        """
        Retrieve latest event of a training experiment
        """
        event = self.get_object(tid)
        serializer = EventDetailSerializer(event)
        return Response(serializer.data)

    def put(self, request, tid, format=None):
        """
        Update latest event of a training experiment
        """
        event = self.get_object(tid)
        serializer = EventDetailSerializer(event, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

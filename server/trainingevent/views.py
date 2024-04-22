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
            return TrainingEvent.objects.filter(training_exp__id=tid)
        except TrainingEvent.DoesNotExist:
            raise Http404

    def get(self, request, tid, format=None):
        """
        Retrieve events of a training experiment
        """
        event = self.get_object(tid)
        serializer = EventDetailSerializer(event, many=True)
        return Response(serializer.data)

    def put(self, request, tid, format=None):
        """
        Update latest event of a training experiment
        """
        event = self.get_object(tid).order_by("-created_at").first()
        serializer = EventDetailSerializer(event, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

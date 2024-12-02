from .models import ExperimentAggregator
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .permissions import IsAdmin, IsAggregatorOwner, IsExpOwner
from .serializers import (
    ExperimentAggregatorListSerializer,
    AggregatorApprovalSerializer,
)


class ExperimentAggregatorList(GenericAPIView):
    permission_classes = [IsAdmin | IsExpOwner | IsAggregatorOwner]
    serializer_class = ExperimentAggregatorListSerializer
    queryset = ""

    def post(self, request, format=None):
        """
        Associate a aggregator to a training_exp
        """
        serializer = ExperimentAggregatorListSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(initiated_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AggregatorApproval(GenericAPIView):
    serializer_class = AggregatorApprovalSerializer
    queryset = ""

    def get_permissions(self):
        self.permission_classes = [IsAdmin | IsExpOwner | IsAggregatorOwner]
        if self.request.method == "DELETE":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

    def get_object(self, aggregator_id, training_exp_id):
        try:
            return ExperimentAggregator.objects.filter(
                aggregator__id=aggregator_id, training_exp__id=training_exp_id
            )
        except ExperimentAggregator.DoesNotExist:
            raise Http404

    def get(self, request, pk, tid, format=None):
        """
        Retrieve approval status of training_exp aggregator associations
        """
        training_expaggregator = (
            self.get_object(pk, tid).order_by("-created_at").first()
        )
        serializer = AggregatorApprovalSerializer(training_expaggregator)
        return Response(serializer.data)

    def put(self, request, pk, tid, format=None):
        """
        Update approval status of the last training_exp aggregator association
        """
        training_expaggregator = (
            self.get_object(pk, tid).order_by("-created_at").first()
        )
        serializer = AggregatorApprovalSerializer(
            training_expaggregator, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, tid, format=None):
        """
        Delete a training_exp aggregator association
        """
        training_expaggregator = self.get_object(pk, tid)
        training_expaggregator.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

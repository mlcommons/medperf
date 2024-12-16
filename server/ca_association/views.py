from .models import ExperimentCA
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from .permissions import IsAdmin, IsCAOwner, IsExpOwner
from .serializers import (
    ExperimentCAListSerializer,
    CAApprovalSerializer,
)


class ExperimentCAList(GenericAPIView):
    permission_classes = [IsAdmin | IsExpOwner | IsCAOwner]
    serializer_class = ExperimentCAListSerializer
    queryset = ""

    def post(self, request, format=None):
        """
        Associate a ca to a training_exp
        """
        serializer = ExperimentCAListSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(initiated_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CAApproval(GenericAPIView):
    serializer_class = CAApprovalSerializer
    queryset = ""

    def get_permissions(self):
        self.permission_classes = [IsAdmin | IsExpOwner | IsCAOwner]
        if self.request.method == "DELETE":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

    def get_object(self, ca_id, training_exp_id):
        try:
            return ExperimentCA.objects.filter(
                ca__id=ca_id, training_exp__id=training_exp_id
            )
        except ExperimentCA.DoesNotExist:
            raise Http404

    def get(self, request, pk, tid, format=None):
        """
        Retrieve approval status of training_exp ca associations
        """
        training_expca = self.get_object(pk, tid).order_by("-created_at").first()
        serializer = CAApprovalSerializer(training_expca)
        return Response(serializer.data)

    def put(self, request, pk, tid, format=None):
        """
        Update approval status of the last training_exp ca association
        """
        training_expca = self.get_object(pk, tid).order_by("-created_at").first()
        serializer = CAApprovalSerializer(
            training_expca, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, tid, format=None):
        """
        Delete a training_exp ca association
        """
        training_expca = self.get_object(pk, tid)
        training_expca.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

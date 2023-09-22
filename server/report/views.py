from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .models import Report
from .permissions import IsAdmin, IsReportOwner, IsBenchmarkOwner, IsMlCubeOwner
from .serializers import ReportSerializer, ReportDetailSerializer


class ReportList(GenericAPIView):
    serializer_class = ReportSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "GET":
            self.permission_classes = [IsAdmin]
        return super(self.__class__, self).get_permissions()

    @extend_schema(operation_id="reports_retrieve_all")
    def get(self, request, format=None):
        """
        List all reports
        """
        reports = Report.objects.all()
        reports = self.paginate_queryset(reports)
        serializer = ReportSerializer(reports, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request, format=None):
        """
        Creates a new report
        """
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReportDetail(GenericAPIView):
    serializer_class = ReportDetailSerializer
    queryset = ""

    def get_permissions(self):
        if self.request.method == "PUT":
            self.permission_classes = [IsAdmin | IsReportOwner]
        elif self.request.method == "DELETE":
            self.permission_classes = [IsAdmin]
        elif self.request.method == "GET":
            self.permission_classes = [
                IsAdmin | IsReportOwner | IsBenchmarkOwner | IsMlCubeOwner
            ]

        return super(self.__class__, self).get_permissions()

    def get_object(self, pk):
        try:
            return Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve a report instance.
        """
        report = self.get_object(pk)
        serializer = ReportDetailSerializer(report)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a report instance.
        """
        report = self.get_object(pk)
        serializer = ReportDetailSerializer(report, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete a report instance.
        """
        report = self.get_object(pk)
        report.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

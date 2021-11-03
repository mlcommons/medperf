from .models import BenchmarkUser
from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from .serializers import (
    BenchmarkUserListSerializer,
    BenchmarkRoleSerializer,
    RoleSerializer,
)


class BenchmarkUserList(GenericAPIView):
    serializer_class = BenchmarkUserListSerializer
    queryset = ""

    @swagger_auto_schema(operation_id="users_benchmarks_list_all")
    def get(self, request, format=None):
        """
        List all users associated across benchmarks
        """
        benchmarkusers = BenchmarkUser.objects.all()
        serializer = BenchmarkUserListSerializer(benchmarkusers, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """
        Associate a user to a benchmark
        """
        serializer = BenchmarkUserListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BenchmarkRole(GenericAPIView):
    serializer_class = BenchmarkRoleSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return BenchmarkUser.objects.filter(user__id=pk)
        except BenchmarkUser.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve all benchmarks associated with a user
        """
        benchmarkuser = self.get_object(pk)
        serializer = BenchmarkRoleSerializer(benchmarkuser, many=True)
        return Response(serializer.data)

    # def put(self, request, pk, format=None):
    #    """
    #    Update the benchmark association with a user
    #    """
    #    if serializer.is_valid():

    # def delete(self, request, pk, format=None):
    #    """
    #    Delete a benchmark association with a user
    #    """


class Role(GenericAPIView):
    serializer_class = RoleSerializer
    queryset = ""

    def get_object(self, user_id, benchmark_id):
        try:
            return BenchmarkUser.objects.filter(
                user__id=user_id, benchmark__id=benchmark_id
            )
        except BenchmarkUser.DoesNotExist:
            raise Http404

    def get(self, request, pk, bid, format=None):
        """
        Retrieve user role of benchmark user association
        """
        benchmarkuser = self.get_object(pk, bid)
        serializer = RoleSerializer(benchmarkuser, many=True)
        return Response(serializer.data)

    # def put(self, request, pk, bid, format=None):
    #    """
    #    Update user role of benchmark user association
    #    """
    #    if serializer.is_valid():

    def delete(self, request, pk, bid, format=None):
        """
        Delete a benchmark user association
        """
        benchmarkuser = self.get_object(pk, bid)
        benchmarkuser.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

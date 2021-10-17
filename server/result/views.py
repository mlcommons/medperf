from django.http import Http404
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from .models import ModelResult
from .serializers import ModelResultSerializer


class ModelResultList(GenericAPIView):
    serializer_class = ModelResultSerializer
    queryset = ""

    def get(self, request, format=None):
        """
        List all results
        """
        modelresults = ModelResult.objects.all()
        serializer = ModelResultSerializer(modelresults, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """
        Creates a new result
        """
        serializer = ModelResultSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModelResultDetail(GenericAPIView):
    serializer_class = ModelResultSerializer
    queryset = ""

    def get_object(self, pk):
        try:
            return ModelResult.objects.get(pk=pk)
        except ModelResult.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Retrieve a result instance.
        """
        modelresult = self.get_object(pk)
        serializer = ModelResultSerializer(modelresult)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a result instance.
        """
        modelresult = self.get_object(pk)
        serializer = ModelResultSerializer(modelresult, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete a result instance.
        """
        modelresult = self.get_object(pk)
        modelresult.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

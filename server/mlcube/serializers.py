from rest_framework import serializers
from .models import MlCube


class MlCubeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MlCube
        fields = "__all__"
        read_only_fields = ["owner"]

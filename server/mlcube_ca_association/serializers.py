from rest_framework import serializers
from .models import ContainerCA


class ContainerCASerializer(serializers.ModelSerializer):
    class Meta:
        model = ContainerCA
        fields = "__all__"
        read_only_fields = ["owner"]

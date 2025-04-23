from rest_framework import serializers
from .models import CA


class CASerializer(serializers.ModelSerializer):
    class Meta:
        model = CA
        fields = "__all__"
        read_only_fields = ["owner"]

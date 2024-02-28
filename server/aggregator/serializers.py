from rest_framework import serializers
from .models import Aggregator


class AggregatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aggregator
        fields = "__all__"
        read_only_fields = ["owner"]
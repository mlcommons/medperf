from rest_framework import serializers
from .models import KBS


class KBSSerializer(serializers.ModelSerializer):
    class Meta:
        model = KBS
        fields = "__all__"
        read_only_fields = ["owner"]

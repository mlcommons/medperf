from rest_framework import serializers
from .models import ModelCAEncryptedKey


class EncryptedKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelCAEncryptedKey
        fields = "__all__"
        read_only_fields = ["owner"]

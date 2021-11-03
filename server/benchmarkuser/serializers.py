from rest_framework import serializers
from .models import BenchmarkUser


class BenchmarkUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkUser
        fields = ["user", "benchmark", "role", "created_at", "modified_at"]


class BenchmarkRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkUser
        fields = ["benchmark", "role", "created_at", "modified_at"]


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenchmarkUser
        fields = ["role", "created_at", "modified_at"]

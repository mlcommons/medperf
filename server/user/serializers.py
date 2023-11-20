from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


# TODO: define what can be edited, and how. Keep in mind
#       that some of these information is stored in Auth0
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
        )

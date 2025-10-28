from rest_framework import serializers
from .models import DataPrepWorkflow


class DataPrepWorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataPrepWorkflow
        fields = "__all__"
        read_only_fields = ["owner"]

    def validate(self, data):
        tarball_url = data.get("prep_tarball_url", "")
        tarball_hash = data.get("prep_tarball_hash", "")

        # validate nonblank parameters file hash
        if tarball_url and not tarball_hash:
            raise serializers.ValidationError("Preparation tarball requires file hash")

        if not tarball_url and tarball_hash:
            raise serializers.ValidationError(
                "preparation tarball hash was provided without URL"
            )

        return data

from rest_framework.permissions import BasePermission
from .models import DataPrepWorkflow


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsDataPrepWorkflowOwner(BasePermission):
    def get_object(self, pk):
        try:
            return DataPrepWorkflow.objects.get(pk=pk)
        except DataPrepWorkflow.DoesNotExist:
            return None

    def has_permission(self, request, view):
        pk = view.kwargs.get("pk", None)
        if not pk:
            return False
        workflow = self.get_object(pk)
        if not workflow:
            return False
        if workflow.owner.id == request.user.id:
            return True
        else:
            return False

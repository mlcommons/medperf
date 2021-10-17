from rest_framework.permissions import BasePermission
from .models import Benchmark


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsBenchmarkOwner(BasePermission):
    def get_object(self, pk):
        try:
            return Benchmark.objects.get(pk=pk)
        except Benchmark.DoesNotExist:
            raise None

    def has_permission(self, request, view):
        print("Benchmark Owner perms", request.user, "view", view)
        print(view.kwargs)
        pk = view.kwargs.get("pk", None)

        benchmark = self.get_object(pk)
        if not benchmark:
            return False
        print(benchmark, request.user.id, benchmark.owner.id)
        if benchmark.owner.id == request.user.id:
            return True
        else:
            return False

from rest_framework.permissions import BasePermission
from django.db import models
from typing import Union, Optional
from rest_framework.request import Request


class IsOwnerOfAnotherObject(BasePermission):
    """
    Unfortunately ABC appears to be incompatible with BasePermission :(
    So I just used NotImplementedErrors here.
    """

    @property
    def another_object(self) -> type[models.Model]:
        """Model of which this use is an owner"""
        raise NotImplementedError

    def get_object(self, pk: str) -> Union[models.Model, None]:
        try:
            return self.another_object.objects.get(pk=pk)
        except self.another_object.DoesNotExist:
            return None

    def is_owner_of_another_object(self, pk: Optional[int], request: Request) -> bool:
        """Note: Assumes Model has an owner field!"""
        if pk is None:
            return False

        model: models.Model = self.get_object(pk)
        if not model:
            return False

        return model.owner.id == request.user.id

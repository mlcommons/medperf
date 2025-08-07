from rest_framework.permissions import BasePermission
from django.db import models
from typing import Union
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

    @property
    def post_request_pk_field(self) -> str:
        """Key in a post request corresponding to the primary key of base_object"""
        raise NotImplementedError

    def get_object(self, pk: str) -> Union[models.Model, None]:
        try:
            return self.another_object.objects.get(pk=pk)
        except self.another_object.DoesNotExist:
            return None

    def is_owner_of_another_object(self, request: Request) -> bool:
        """Note: Assumes Model has an owner field!"""
        pk = request.data.get(self.post_request_pk_field, None)
        if not pk:
            return False

        model: models.Model = self.get_object(pk)
        if not model:
            return False

        return model.owner.id == request.user.id

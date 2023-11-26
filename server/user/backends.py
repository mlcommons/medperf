from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.settings import api_settings
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object


def __get_email_from_token(validated_token):
    try:
        return validated_token[settings.TOKEN_USER_EMAIL_CLAIM]
    except KeyError:
        raise InvalidToken(_("Token must contain the user email address"))


class JWTAuthenticateOrCreateUser(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_("Token contained no recognizable user identification"))

        try:
            user = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            user_email = __get_email_from_token(validated_token)
            user = self.user_model.objects.create_user(
                **{api_settings.USER_ID_FIELD: user_id}, email=user_email
            )

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")

        return user


class JWTScheme(OpenApiAuthenticationExtension):
    target_class = "user.backends.JWTAuthenticateOrCreateUser"
    name = "JWTAuth"
    match_subclasses = True
    priority = -1

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name="Authorization",
            token_prefix=api_settings.AUTH_HEADER_TYPES[0],
        )

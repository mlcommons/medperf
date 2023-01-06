"""medperf URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, re_path, path
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf import settings

from utils.views import ServerAPIVersion

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(api_version=settings.SERVER_API_VERSION), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(), name="swagger-ui"),
    re_path(r"^$", SpectacularRedocView.as_view(), name="redoc"),
    path("admin/", admin.site.urls, name="admin"),
    path("version", ServerAPIVersion.as_view(), name="get-version"),
    path('api/', include([
        path('v1/', include([
            path("benchmarks/", include("benchmark.urls", namespace="v1"), name="benchmark"),
            path("mlcubes/", include("mlcube.urls", namespace="v1"), name="mlcube"),
            path("datasets/", include("dataset.urls", namespace="v1"), name="dataset"),
            path("results/", include("result.urls", namespace="v1"), name="result"),
            path("users/", include("user.urls", namespace="v1"), name="users"),
            path("me/", include("utils.urls", namespace="v1"), name="me"),
            path("auth-token/", obtain_auth_token, name="auth-token"),
        ])),
    ])),
]

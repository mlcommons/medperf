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
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf import settings

from utils.views import ServerAPIVersion

API_VERSION = settings.SERVER_API_VERSION
API_PREFIX = 'api/' + API_VERSION + '/'

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(api_version=API_VERSION), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(), name="swagger-ui"),
    re_path(r"^$", SpectacularRedocView.as_view(), name="redoc"),
    path("admin/", admin.site.urls, name="admin"),
    path("version", ServerAPIVersion.as_view(), name="get-version"),
    path(API_PREFIX, include([
        path("benchmarks/", include("benchmark.urls", namespace=API_VERSION), name="benchmark"),
        path("mlcubes/", include("mlcube.urls", namespace=API_VERSION), name="mlcube"),
        path("datasets/", include("dataset.urls", namespace=API_VERSION), name="dataset"),
        path("results/", include("execution.urls", namespace=API_VERSION), name="result"),  # Kept for backwards compatibility
        path("executions/", include("execution.urls", namespace=API_VERSION), name="result"),
        path("users/", include("user.urls", namespace=API_VERSION), name="users"),
        path("me/", include("utils.urls", namespace=API_VERSION), name="me"),
    ])),
]

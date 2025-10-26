from django.urls import path
from . import views

app_name = "MLCubeKey"

urlpatterns = [
    path("", views.GetAllEncryptedKeys.as_view()),
    path("<int:pk>/", views.GetEncryptedKeyById.as_view()),
    path("bulk/", views.PostMultipleEncryptedKeys.as_view()),
]

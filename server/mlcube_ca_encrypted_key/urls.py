from django.urls import path
from . import views

app_name = "MLCube"

urlpatterns = [
    path("", views.GetAllEncryptedKeys.as_view()),
    path("<int:pk>/", views.GetEncryptedKeyById.as_view()),
]

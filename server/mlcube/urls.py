from django.urls import path
from . import views

app_name = "MLCube"

urlpatterns = [
    path("", views.MlCubeList.as_view()),
    path("<int:pk>/", views.MlCubeDetail.as_view()),
    path("<int:pk>/datasets/", views.MlCubeDatasetList.as_view()),
    path("<int:pk>/model/", views.MlCubeModel.as_view()),
]

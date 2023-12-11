from django.urls import path
from . import views

app_name = "MyUser"

urlpatterns = [
    path("", views.User.as_view()),
    path("benchmarks/", views.BenchmarkList.as_view()),
    path("datasets/", views.DatasetList.as_view()),
    path("mlcubes/", views.MlCubeList.as_view()),
    path("results/", views.ModelResultList.as_view()),
    path("datasets/associations/", views.DatasetAssociationList.as_view()),
    path("mlcubes/associations/", views.MlCubeAssociationList.as_view()),
]

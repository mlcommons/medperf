from django.urls import path
from . import views


urlpatterns = [
    path("", views.BenchmarkList.as_view()),
    path("<int:pk>/", views.BenchmarkDetail.as_view()),
    path("<int:pk>/models/", views.BenchmarkModelList.as_view()),
    path("<int:pk>/datasets/", views.BenchmarkDatasetList.as_view()),
    path("<int:pk>/results/", views.BenchmarkResultList.as_view()),
    path("<int:pk>/benchmarkmodels/", views.BenchmarkModelAssociationList.as_view()),
]

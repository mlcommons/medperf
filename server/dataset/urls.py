from django.urls import path
from . import views
from benchmarkdataset import views as bviews

urlpatterns = [
    path("", views.DatasetList.as_view()),
    path("<int:pk>/", views.DatasetDetail.as_view()),
    path("benchmarks/", bviews.BenchmarkDatasetList.as_view()),
    path("<int:pk>/benchmarks/", bviews.BenchmarkDatasetApproval.as_view()),
    path("<int:pk>/benchmarks/<int:bid>/", bviews.DatasetApproval.as_view()),
]

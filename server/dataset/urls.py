from django.urls import path
from . import views
from benchmarkdataset import views as bviews

app_name = "Dataset"

urlpatterns = [
    path("", views.DatasetList.as_view()),
    path("<int:pk>/", views.DatasetDetail.as_view()),
    path("benchmarks/", bviews.BenchmarkDatasetList.as_view()),
    path("<int:pk>/benchmarks/<int:bid>/", bviews.DatasetApproval.as_view()),
    # path("<int:pk>/benchmarks/", bviews.DatasetBenchmarksList.as_view()),
    # TODO: when activating this endpoint later, check permissions and write tests
]

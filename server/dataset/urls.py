from django.urls import path
from . import views
from benchmarkdataset import views as bviews
from traindataset_association import views as tviews

app_name = "Dataset"

urlpatterns = [
    path("", views.DatasetList.as_view()),
    path("<int:pk>/", views.DatasetDetail.as_view()),
    path("benchmarks/", bviews.BenchmarkDatasetList.as_view()),
    path("<int:pk>/benchmarks/<int:bid>/", bviews.DatasetApproval.as_view()),
    # path("<int:pk>/benchmarks/", bviews.DatasetBenchmarksList.as_view()),
    # path("<int:pk>/training/", tviews.DatasetExperimentList.as_view()),
    # NOTE: when activating those two endpoints later, check permissions and write tests
    path("training/", tviews.ExperimentDatasetList.as_view()),
    path("<int:pk>/training/<int:tid>/", tviews.DatasetApproval.as_view()),
]

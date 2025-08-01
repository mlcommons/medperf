from django.urls import path
from benchmarkmodel import views as bviews
from mlcube_ca_association import views as mlcube_ca_views
from . import views

app_name = "MLCube"

urlpatterns = [
    path("", views.MlCubeList.as_view()),
    path("<int:pk>/", views.MlCubeDetail.as_view()),
    path("benchmarks/", bviews.BenchmarkModelList.as_view()),
    path("<int:pk>/benchmarks/<int:bid>/", bviews.ModelApproval.as_view()),
    path("<int:pk>/datasets/", views.MlCubeDatasetList.as_view()),
    path("<int:pk>/cas/", mlcube_ca_views.ContainerCAList.as_view()),
    path("<int:pk>/cas/<int:bid>/", mlcube_ca_views.CertificateDetail.as_view()),
    # path("<int:pk>/benchmarks/", bviews.ModelBenchmarksList.as_view()),
    # NOTE: when activating this endpoint later, check permissions and write tests
]

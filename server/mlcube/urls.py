from django.urls import path
from benchmarkmodel import views as bviews

from mlcube_ca_encrypted_key import views as key_views
from . import views

app_name = "MLCube"

urlpatterns = [
    path("", views.MlCubeList.as_view()),
    path("<int:pk>/", views.MlCubeDetail.as_view()),
    path("benchmarks/", bviews.BenchmarkModelList.as_view()),
    path("<int:pk>/benchmarks/<int:bid>/", bviews.ModelApproval.as_view()),
    path("<int:pk>/datasets/", views.MlCubeDatasetList.as_view()),
    path("<int:model_id>/ca/", views.GetCAFromContainer.as_view()),
    path(
        "<int:model_id>/ca/<int:certificate_id>/keys/",
        key_views.GetEncryptedKeyFromModelAndCA.as_view(),
    ),
    path("<int:model_id>/keys/", key_views.GetEncryptedKeyFromModel.as_view()),
    path('keys/', key_views.PostMultipleEncryptedKeys.as_view())
    # path("<int:pk>/benchmarks/", bviews.ModelBenchmarksList.as_view()),
    # NOTE: when activating this endpoint later, check permissions and write tests
]

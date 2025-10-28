from django.urls import path
from . import views

app_name = "DataPrepWorkflow"

urlpatterns = [
    path("", views.DataPrepWorkflowList.as_view()),
    path("<int:pk>/", views.DataPrepWorkflowDetail.as_view()),
    path("<int:pk>/datasets/", views.DataPrepWorkflowDatasetList.as_view()),
    # path("<int:pk>/benchmarks/", bviews.ModelBenchmarksList.as_view()),
    # NOTE: when activating this endpoint later, check permissions and write tests
]

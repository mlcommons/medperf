from django.urls import path
from benchmarkmodel import views as bviews
from . import views

app_name = "Model"

urlpatterns = [
    path("", views.ModelList.as_view()),
    path("<int:pk>/", views.ModelDetail.as_view()),
    path("benchmarks/", bviews.BenchmarkModelList.as_view()),
    path("<int:pk>/benchmarks/<int:bid>/", bviews.ModelApproval.as_view()),
    path("<int:pk>/benchmarks/", bviews.ModelBenchmarksList.as_view()),
]

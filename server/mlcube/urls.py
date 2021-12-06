from django.urls import path
from benchmarkmodel import views as bviews
from . import views

urlpatterns = [
    path("", views.MlCubeList.as_view()),
    path("<int:pk>/", views.MlCubeDetail.as_view()),
    path("benchmarks/", bviews.BenchmarkModelList.as_view()),
    path("<int:pk>/benchmarks/", bviews.BenchmarkModelApproval.as_view()),
    path("<int:pk>/benchmarks/<int:bid>/", bviews.ModelApproval.as_view()),
]

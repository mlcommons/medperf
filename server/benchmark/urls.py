from django.urls import path
from . import views
from certificate import views as certificate_views

app_name = "Benchmark"

urlpatterns = [
    path("", views.BenchmarkList.as_view()),
    path("<int:pk>/", views.BenchmarkDetail.as_view()),
    path("<int:pk>/models/", views.BenchmarkModelList.as_view()),
    path("<int:pk>/datasets/", views.BenchmarkDatasetList.as_view()),
    path("<int:pk>/results/", views.BenchmarkResultList.as_view()),
    path("<int:pk>/participants_info/", views.ParticipantsInfo.as_view()),
    path(
        "<int:benchmark_id>/models/<int:model_id>/cas/<int:ca_id>",
        certificate_views.CertificatesFromBenchmark.as_view(),
    ),
]

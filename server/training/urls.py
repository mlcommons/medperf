from django.urls import path
from . import views

app_name = "training"

urlpatterns = [
    path("", views.TrainingExperimentList.as_view()),
    path("<int:pk>/", views.TrainingExperimentDetail.as_view()),
    path("<int:pk>/datasets/", views.TrainingDatasetList.as_view()),
    path("<int:pk>/aggregator/", views.GetAggregator.as_view()),
]

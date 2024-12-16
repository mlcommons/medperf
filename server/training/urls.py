from django.urls import path, include
from . import views

app_name = "training"

urlpatterns = [
    path("", views.TrainingExperimentList.as_view()),
    path("<int:pk>/", views.TrainingExperimentDetail.as_view()),
    path("<int:pk>/datasets/", views.TrainingDatasetList.as_view()),
    path("<int:pk>/aggregator/", views.TrainingAggregator.as_view()),
    path("<int:pk>/ca/", views.TrainingCA.as_view()),
    path("<int:pk>/event/", views.GetTrainingEvent.as_view()),
    path("<int:pk>/participants_info/", views.ParticipantsInfo.as_view()),
    path("events/", include("trainingevent.urls", namespace=app_name), name="event"),
]

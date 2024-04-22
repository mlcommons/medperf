from django.urls import path
from . import views
import trainingevent.views as pviews

app_name = "training"

urlpatterns = [
    path("", views.TrainingExperimentList.as_view()),
    path("<int:pk>/", views.TrainingExperimentDetail.as_view()),
    path("<int:pk>/datasets/", views.TrainingDatasetList.as_view()),
    path("<int:pk>/aggregator/", views.TrainingAggregator.as_view()),
    path("<int:pk>/ca/", views.TrainingCA.as_view()),
    path("<int:tid>/plan/", pviews.EventDetail.as_view()),
    path("plans/", pviews.EventList.as_view()),
]

from django.urls import path
from . import views
from aggregator_association import views as aviews

app_name = "aggregator"

urlpatterns = [
    path("", views.AggregatorList.as_view()),
    path("<int:pk>/", views.AggregatorDetail.as_view()),
    path("training_experiments/", aviews.ExperimentAggregatorList.as_view()),
    path("<int:pk>/training_experiments/<int:tid>/", aviews.AggregatorApproval.as_view()),
]
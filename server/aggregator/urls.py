from django.urls import path
from . import views
import aggregator_association.views as tviews

app_name = "aggregator"

urlpatterns = [
    path("", views.AggregatorList.as_view()),
    path("<int:pk>/", views.AggregatorDetail.as_view()),
    path("training/", tviews.ExperimentAggregatorList.as_view()),
    path("<int:pk>/training/<int:tid>/", tviews.AggregatorApproval.as_view()),
]

from django.urls import path
from . import views

app_name = "aggregator"

urlpatterns = [
    path("", views.AggregatorList.as_view()),
    path("<int:pk>/", views.AggregatorDetail.as_view()),
]

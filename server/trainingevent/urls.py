from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventList.as_view()),
    path("<int:pk>/", views.EventDetail.as_view()),
]

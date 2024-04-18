from django.urls import path
from . import views

app_name = "ca"

urlpatterns = [
    path("", views.CAList.as_view()),
    path("<int:pk>/", views.CADetail.as_view()),
]

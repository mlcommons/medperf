from django.urls import path
from . import views

app_name = "Execution"

urlpatterns = [
    path("", views.ExecutionList.as_view()),
    path("<int:pk>/", views.ExecutionDetail.as_view()),
]

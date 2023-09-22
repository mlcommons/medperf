from django.urls import path
from . import views

app_name = "Report"

urlpatterns = [
    path("", views.ReportList.as_view()),
    path("<int:pk>/", views.ReportDetail.as_view()),
]

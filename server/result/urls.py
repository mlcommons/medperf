from django.urls import path
from . import views

app_name = "Result"

urlpatterns = [
    path("", views.ModelResultList.as_view()),
    path("<int:pk>/", views.ModelResultDetail.as_view()),
]

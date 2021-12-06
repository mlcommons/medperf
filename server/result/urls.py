from django.urls import path
from . import views


urlpatterns = [
    path("", views.ModelResultList.as_view()),
    path("<int:pk>/", views.ModelResultDetail.as_view()),
]

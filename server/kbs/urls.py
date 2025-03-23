from django.urls import path
from . import views

app_name = "kbs"

urlpatterns = [
    path("", views.KBSList.as_view()),
    path("<int:pk>/", views.KBSDetail.as_view()),
]

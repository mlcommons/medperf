from django.urls import path
from . import views


app_name = "ca"

urlpatterns = [
    path("", views.CertificateList.as_view()),
    path("<int:pk>/", views.CertificateDetail.as_view()),
]

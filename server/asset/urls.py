from django.urls import path
from . import views

app_name = "Asset"

urlpatterns = [
    path("", views.AssetList.as_view()),
    path("<int:pk>/", views.AssetDetail.as_view()),
]

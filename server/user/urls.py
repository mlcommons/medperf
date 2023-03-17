from django.urls import path
from . import views

app_name = "User"

urlpatterns = [
    path("", views.UserList.as_view()),
    path("<int:pk>/", views.UserDetail.as_view()),
]

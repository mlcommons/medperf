from django.urls import path
from benchmarkuser import views as bviews
from . import views

urlpatterns = [
    path("", views.UserList.as_view()),
    path("<int:pk>/", views.UserDetail.as_view()),
    path("benchmarks/", bviews.BenchmarkUserList.as_view()),
    path("<int:pk>/benchmarks/", bviews.BenchmarkRole.as_view()),
    path("<int:pk>/benchmarks/<int:bid>/", bviews.Role.as_view()),
]

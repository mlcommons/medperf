from django.urls import path
from . import views
import ca_association.views as tviews

app_name = "ca"

urlpatterns = [
    path("", views.CAList.as_view()),
    path("<int:pk>/", views.CADetail.as_view()),
    path("training/", tviews.ExperimentCAList.as_view()),
    path("<int:pk>/training/<int:tid>/", tviews.CAApproval.as_view()),
]

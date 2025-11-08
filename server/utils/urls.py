from django.urls import path
from . import views

app_name = "MyUser"

urlpatterns = [
    path("", views.User.as_view()),
    path("benchmarks/", views.BenchmarkList.as_view()),
    path("datasets/", views.DatasetList.as_view()),
    path("mlcubes/", views.MlCubeList.as_view()),
    path("results/", views.ModelResultList.as_view()),
    path("training/", views.TrainingExperimentList.as_view()),
    path("aggregators/", views.AggregatorList.as_view()),
    path("training/events/", views.TrainingEventList.as_view()),
    path("cas/", views.CAList.as_view()),
    path("datasets/associations/", views.DatasetAssociationList.as_view()),
    path("mlcubes/associations/", views.MlCubeAssociationList.as_view()),
    path(
        "datasets/training_associations/",
        views.DatasetTrainingAssociationList.as_view(),
    ),
    path(
        "aggregators/training_associations/", views.AggregatorAssociationList.as_view()
    ),
    path("certificates/", views.CertificateList.as_view()),
    path("encrypted_keys/", views.EncryptedKeyList.as_view()),
]

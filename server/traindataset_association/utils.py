from django.db.models import OuterRef, Subquery
from .models import ExperimentDataset


def latest_data_associations(training_exp_id):
    experiment_datasets = ExperimentDataset.objects.filter(
        training_exp__id=training_exp_id
    )
    latest_assocs = (
        experiment_datasets.filter(dataset=OuterRef("dataset"))
        .order_by("-created_at")
        .values("id")[:1]
    )
    return experiment_datasets.filter(id__in=Subquery(latest_assocs))

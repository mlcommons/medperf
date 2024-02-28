from django.db.models import OuterRef, Subquery
from .models import ExperimentAggregator


def latest_agg_associations(training_exp_id):
    experiment_aggregators = ExperimentAggregator.objects.filter(
        training_exp__id=training_exp_id
    )
    latest_assocs = (
        experiment_aggregators.filter(aggregator=OuterRef("aggregator"))
        .order_by("-created_at")
        .values("id")[:1]
    )
    return experiment_aggregators.filter(id__in=Subquery(latest_assocs))

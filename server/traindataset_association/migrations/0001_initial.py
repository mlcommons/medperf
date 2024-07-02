# Generated by Django 4.2.11 on 2024-04-29 13:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("dataset", "0004_auto_20231211_1827"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ExperimentDataset",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("metadata", models.JSONField(default=dict)),
                (
                    "approval_status",
                    models.CharField(
                        choices=[
                            ("PENDING", "PENDING"),
                            ("APPROVED", "APPROVED"),
                            ("REJECTED", "REJECTED"),
                        ],
                        default="PENDING",
                        max_length=100,
                    ),
                ),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "dataset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="dataset.dataset",
                    ),
                ),
                (
                    "initiated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["modified_at"],
            },
        ),
    ]
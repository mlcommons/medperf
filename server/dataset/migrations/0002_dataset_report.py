# Generated by Django 3.2.20 on 2023-12-07 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataset', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='report',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
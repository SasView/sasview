# Generated by Django 4.2.2 on 2023-07-11 18:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("analyze", "0001_version"),
    ]

    operations = [
        migrations.CreateModel(
            name="FitModel",
            fields=[
                (
                    "analysismodelbase_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="analyze.analysismodelbase",
                    ),
                ),
                (
                    "polydispersity",
                    models.BooleanField(
                        default=False,
                        help_text="Is polydispersity being checked in this model",
                    ),
                ),
                (
                    "magnetism",
                    models.BooleanField(
                        default=False,
                        help_text="Is magnetism being checked in this model?",
                    ),
                ),
                (
                    "Qminimum",
                    models.FloatField(
                        blank=True, help_text="Minimum Q value for the fit"
                    ),
                ),
                (
                    "Qmaximum",
                    models.FloatField(
                        blank=True, help_text="Maximum Q value for the fit"
                    ),
                ),
                ("model", models.CharField(help_text="model string", max_length=256)),
            ],
            bases=("analyze.analysismodelbase",),
        ),
        migrations.CreateModel(
            name="FitParameter",
            fields=[
                (
                    "analysisparameterbase_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="analyze.analysisparameterbase",
                    ),
                ),
                (
                    "polydisperse",
                    models.BooleanField(
                        default=False, help_text="Is this a polydisperse parameter?"
                    ),
                ),
                (
                    "magnetic",
                    models.BooleanField(
                        default=False, help_text="is this a magnetic parameter?"
                    ),
                ),
            ],
            bases=("analyze.analysisparameterbase",),
        ),
        migrations.CreateModel(
            name="Fit",
            fields=[
                (
                    "analysisbase_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="analyze.analysisbase",
                    ),
                ),
                (
                    "status",
                    models.IntegerField(
                        choices=[(1, "Queued"), (2, "Running"), (3, "Complete")],
                        default=False,
                    ),
                ),
            ],
            bases=("analyze.analysisbase",),
        ),
    ]
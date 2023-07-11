from django.db import migrations, models
from analyze.fitting.models import Fit


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("analyze", "0001_version"),
    ]

    operations = [
        migrations.CreateModel(
            name='Fit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('results', models.CharField(blank=True)),
                ('is_public', models.BooleanField(default = False)),
                ("status", models.IntegerField(
                    choices=[(1, "Queued"), (2, "Running"), (3, "Complete")],
                    default=False)),
            ],
        ),
        migrations.CreateModel(
            name='FitModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('polydispersity', models.BooleanField(default = False)),
                ('magnetism', models.BooleanField(default=False)),
                ('Qminimum', models.FloatField(blank = True)),
                ('Qmaximum', models.FloatField(blank = True)),
                ('model', models.CharField(max_length=256)),
                ('online_model_url', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='FitParameter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unit', models.CharField(blank=False)),
                ('polydisperse', models.BooleanField(default=False)),
                ('magnetic', models.BooleanField(default=False))
            ]
        ),
    ]

from django.db import migrations, models
from analyze.fitting.models import Fit


class Migration(migrations.Migration):

    initial = True

    operations = [
        migrations.CreateModel(
            name='Fit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('results', models.CharField(blank=True)),
                ('is_public', models.BooleanField(default = False)),
                ('status', models.IntegerField(choices=Fit.StatusChoices))
            ],
        ),
        migrations.CreateModel(
            name='FitModel',
            fields=[
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
                ('unit', models.CharField(blank=False)),
                ('polydisperse', models.BooleanField(default=False)),
                ('magnetic', models.BooleanField(default=False))
            ]
        ),
    ]

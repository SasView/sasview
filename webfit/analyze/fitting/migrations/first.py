from django.db import migrations, models
from models import Fit


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        'Analysis'
    ]

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
            ],
        ),
        migrations.CreateModel(
            name='FitParameter',
            fields=[
                ('name', models.CharField(max_length=300))
            ]
        ),
    ]

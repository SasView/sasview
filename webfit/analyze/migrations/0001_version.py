from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("user_app", "0001_version"),
        ("data", "0001_version"),
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisBase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_user', models.ForeignKey(default = None, primary_key=False, to='user_app.UserProfile', on_delete=models.CASCADE)),
                ('data_id', models.ForeignKey(default = None, primary_key=False, on_delete=models.CASCADE, to='data.Data')),
                ('model_id', models.ForeignKey(default = None, primary_key=False, on_delete=models.CASCADE, to='analyze.AnalysisModelBase')),
                ('gpu_requested', models.BooleanField(default = False)),
                ('time_recieved', models.DateTimeField(auto_now_add=True)),
                ('time_started', models.DateTimeField(auto_now=False, blank=True, null=True)),
                ('time_complete', models.DateTimeField(auto_now=False, blank=True, null=True)),
                ('analysis_success', models.BooleanField(default = False)),
                ('is_public', models.BooleanField(default = False)),
            ],
        ),
        migrations.CreateModel(
            name='AnalysisModelBase',
            fields=[
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='AnalysisParameterBase',
            fields=[
                ('name', models.CharField(max_length=300)),
                ('value', models.FloatField(blank=False)),
                ('data_type', models.CharField(max_length=100)),
                ('unit', models.CharField(blank=False)),
            ]
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        'Data'
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisBase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.ForeignKey(default = None, null=True, on_delete=models.CASCADE, to='core.User'))
                ('data_id', models.ForeignKey(default = None, primary_key=False, on_delete=models.CASCADE, to='data.Data')),
                ('model_id', models.ForeignKey(default = None, primary_key=False, on_delete=models.CASCADE, to='.AnalysisModelBase'))
                ('gpu_requested', models.BooleanField(default = False)),
                ('time_recieved', models.DateTimeField(auto_now_add=True)),
                ('time_started', models.DateTimeField(auto_now=False, blank=True, null=True)),
                ('time_complete', models.DateTimeField(auto_now=False, blank=True, null=True)),
                ('analysis_success', models.BooleanField(defalt = False)),
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
                ('upper_limit', models.FloatField(blank= True, null=True)),
                ('lower_limit', models.FloatField(blank= True, null=True))
            ]
        ),
    ]

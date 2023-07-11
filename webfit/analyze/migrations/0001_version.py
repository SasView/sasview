from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("user_app", "0001_version"),
        ("data", "0001_version"),
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisParameterBase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, help_text="Parameter Name")),
                ('value', models.FloatField(blank=False, help_text="the value of the parameter")),
                ('data_type', models.CharField(max_length=100, help_text="parameter type (int/double)")),
                ('unit', models.CharField(blank=False, help_text = "string for what unit the parameter is")),
            ]
        ),

        migrations.CreateModel(
            name='AnalysisModelBase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, help_text="name of analysis model")),
                ('parameters', models.ForeignKey(default = None, to="analyze.analysisparameterbase", on_delete=models.CASCADE))
            ],
        ),
        
        migrations.CreateModel(
            name='AnalysisBase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_user', models.ForeignKey(default = None, primary_key=False, to='user_app.UserProfile', on_delete=models.CASCADE)),
                ('data_id', models.ForeignKey(default = None, primary_key=False, on_delete=models.CASCADE, to='data.Datafile')),
                ('model_id', models.ForeignKey(default = None, primary_key=False, on_delete=models.CASCADE, to='analyze.AnalysisModelBase')),
                
                ('gpu_requested', models.BooleanField(default = False, help_text= "use GPU rather than CPU")),
                ('time_recieved', models.DateTimeField(auto_now_add=True, help_text="analysis requested")),
                ('time_started', models.DateTimeField(auto_now=False, blank=True, null=True, help_text="analysis initiated")),
                ('time_complete', models.DateTimeField(auto_now=False, blank=True, null=True, help_text="analysis stopped")),
                ('analysis_success', models.BooleanField(default = False, help_text="Successful completion of analysis")),
                
                ('is_public', models.BooleanField(default = False, help_text="does the user want their data to be public")),
            ],
        ),
    ]

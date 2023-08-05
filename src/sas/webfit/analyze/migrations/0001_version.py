from django.db import migrations, models
from django.conf import settings

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("data", "0001_version"),
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisModelBase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, help_text="name of analysis model")),
            ],
        ),

        migrations.CreateModel(
            name='AnalysisParameterBase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_id', models.ForeignKey(default = None, primary_key=False, on_delete=models.deletion.CASCADE, to='analyze.AnalysisModelBase')),
                ('name', models.CharField(max_length=100, help_text="Parameter Name")),
                ('value', models.FloatField(blank=True, null = True, help_text="the value of the parameter")),
                ('data_type', models.CharField(max_length=100, blank=True, null = True, help_text="parameter type (int/double)")),
                ('unit', models.CharField(max_length=100, blank=True, null = True, help_text = "string for what unit the parameter is")),
                ('lower_limit', models.FloatField(blank=True, help_text="optional lower limit")),
                ('upper_limit', models.FloatField(blank=True, help_text="optional upper limit"))
            ]
        ),
        
        migrations.CreateModel(
            name='AnalysisBase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_user', models.ForeignKey(default=None, blank=True, null=True, to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
                ('data_id', models.ForeignKey(blank=True, null=True, primary_key=False, on_delete=models.deletion.CASCADE, to='data.data')),
                ('model_id', models.ForeignKey(default = None, primary_key=False, on_delete=models.deletion.CASCADE, to='analyze.AnalysisModelBase')),
                
                ('gpu_requested', models.BooleanField(default = False, help_text= "use GPU rather than CPU")),
                ('time_recieved', models.DateTimeField(auto_now_add=True, help_text="analysis requested")),
                ('time_started', models.DateTimeField(auto_now=False, blank=True, null=True, help_text="analysis initiated")),
                ('time_complete', models.DateTimeField(auto_now=False, blank=True, null=True, help_text="analysis stopped")),
                ('analysis_success', models.BooleanField(default = False, help_text="Successful completion of analysis")),
                
                ('is_public', models.BooleanField(default = False, help_text="does the user want their data to be public")),
            ],
        ),
    ]

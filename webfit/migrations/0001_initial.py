from django.db import migrations, models

from data.migrations.first import Migration as DataMigrations
from analyze.migrations.first import Migration as AnalysisMigrations
from analyze.fitting.migrations.first import Migration as FitMigrations


class MigrationAll(migrations.Migration):
    initial = True
    
    operations = [
        AnalysisMigrations.operations,
        DataMigrations.operations,
        FitMigrations.operations,
    ]
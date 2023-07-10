from django.db import migrations, models

from data.migrations.version_0001 import Migration as DataMigrations
from analyze.migrations.version_0001 import Migration as AnalysisMigrations
from analyze.fitting.migrations.version_0001 import Migration as FitMigrations


class MigrationAll(migrations.Migration):
    initial = True
    
    operations = [
        AnalysisMigrations.operations,
        DataMigrations.operations,
        FitMigrations.operations,
    ]
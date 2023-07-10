from analyze.migrations.0001_initial import Migration as AnalysisMigrations


class MigrationAll:
    initial = True
    
    operations = [
        AnalysisMigrations.operations

    ]
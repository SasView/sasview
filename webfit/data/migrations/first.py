from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    operations = [
        migrations.CreateModel(
            name='Data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                #create current_user later
                ('file', models.FileField(null = False)),
                ('save_file_string', models.CharField(max_length=200, null = False)),
                ('is_public', models.BooleanField(default = False)),
            ],
        ),
    ]

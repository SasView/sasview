from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    operations = [
        migrations.CreateModel(
            name='Data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_user', models.ForeignKey(default = None, primary_key=False, to='user_authentication.models.User', on_delete=models.CASCADE)),
                ('file', models.FileField(null = False)),
                ('save_file_string', models.CharField(max_length=200, null = False)),
                ('is_public', models.BooleanField(default = False)),
            ],
        ),
    ]

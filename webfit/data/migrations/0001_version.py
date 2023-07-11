from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("user_app", "0001_version")
    ]

    operations = [
        migrations.CreateModel(
            name='Data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_user', models.ForeignKey(to='user_app.UserProfile', on_delete=models.deletion.CASCADE)),
                ('file', models.FileField(null = False, help_text="This is a file", upload_to="")),
                ('save_file_string', models.CharField(max_length=200, null = False, help_text="File location to save data")),
                ('is_public', models.BooleanField(default = False, help_text= "opt in to submit your data into example pool")),
            ],
        ),
    ]

from django.db import migrations, models
from django.conf import settings

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_user', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=False, null=False, on_delete=models.deletion.CASCADE)),
                ('file', models.FileField(null = False, help_text="This is a file", upload_to="")),
                ('is_public', models.BooleanField(default = False, help_text= "opt in to submit your data into example pool")),
            ],
        ),
    ]

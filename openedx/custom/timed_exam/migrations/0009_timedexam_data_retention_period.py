# Generated by Django 2.2.16 on 2021-02-25 06:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timed_exam', '0008_auto_20210222_0846'),
    ]

    operations = [
        migrations.AddField(
            model_name='timedexam',
            name='data_retention_period',
            field=models.IntegerField(default=10),
        ),
    ]

# Generated by Django 2.2.16 on 2022-06-15 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taleem', '0015_mobile_app_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='mobileapp',
            name='force_update',
            field=models.BooleanField(default=False),
        ),
    ]

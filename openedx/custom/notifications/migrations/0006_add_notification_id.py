# Generated by Django 2.2.16 on 2022-08-17 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0005_course_key_char'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationmessage',
            name='notification_id',
            field=models.UUIDField(blank=True, null=True),
        ),
    ]

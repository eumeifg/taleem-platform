# Generated by Django 2.2.16 on 2022-08-12 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_add_course_key_and_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationmessage',
            name='course_key',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]

# Generated by Django 2.2.16 on 2022-10-27 09:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taleem', '0021_teacher_permissions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ta3leemuserprofile',
            name='can_create_course',
        ),
    ]

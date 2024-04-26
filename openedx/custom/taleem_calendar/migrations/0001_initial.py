# Generated by Django 2.2.16 on 2021-08-23 08:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ta3leemReminder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('course', 'Course'), ('exam', 'Timed Exam'), ('class', 'Live Class')], help_text='Select the reminder type', max_length=24)),
                ('course_id', opaque_keys.edx.django.models.CourseKeyField(blank=True, default=None, max_length=255, null=True)),
                ('class_id', models.UUIDField(blank=True, default=None, null=True)),
                ('message', models.TextField(max_length=255)),
                ('reminder_time', models.DateTimeField(help_text='Time of the reminder to show on calendar or send notification')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

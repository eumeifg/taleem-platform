# Generated by Django 2.2.16 on 2021-01-08 05:17

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TimedExamSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('course_key', models.CharField(max_length=255)),
                ('allotted_time', models.CharField(default='01:00', max_length=255)),
                ('allowed_disconnection_window', models.CharField(max_length=255)),
                ('webcam_monitoring_mode', models.CharField(choices=[('detection', 'detection'), ('detection_and_recognition', 'detection_and_recognition')], max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
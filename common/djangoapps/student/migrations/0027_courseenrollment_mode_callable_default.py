# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-07-19 13:06


import course_modes.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0026_allowedauthuser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseenrollment',
            name='mode',
            field=models.CharField(default=course_modes.models.CourseMode.get_default_mode_slug, max_length=100),
        ),
        migrations.AlterField(
            model_name='historicalcourseenrollment',
            name='mode',
            field=models.CharField(default=course_modes.models.CourseMode.get_default_mode_slug, max_length=100),
        ),
    ]
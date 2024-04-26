# Generated by Django 2.2.16 on 2021-08-26 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taleem_calendar', '0002_auto_20210824_1335'),
    ]

    operations = [
        migrations.AddField(
            model_name='ta3leemreminder',
            name='privacy',
            field=models.CharField(choices=[('public', 'Public'), ('private', 'Private')], default='public', help_text='Privacy to identify if the reminder for all students or specific.', max_length=10),
        ),
        migrations.AlterField(
            model_name='ta3leemreminder',
            name='type',
            field=models.CharField(choices=[('course_start_date', 'Course Start Date'), ('course_start_end', 'Course End Date'), ('exam_start_date', 'Exam Start Date'), ('exam_end_date', 'Exam End Date'), ('live_class', 'Live Class'), ('course_important_date', 'Course Important Date')], help_text='Select the reminder type', max_length=24),
        ),
    ]

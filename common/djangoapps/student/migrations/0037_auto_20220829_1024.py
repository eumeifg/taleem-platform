# Generated by Django 2.2.16 on 2022-08-29 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0036_alter_student_course_enrollment_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='state',
            field=models.CharField(blank=True, choices=[('Al Anbar', 'AN'), ('Babylon', 'BB'), ('Baghdad', 'BG'), ('Basra', 'BA'), ('Dhi Qar', 'DQ'), ('Al-Qādisiyyah', 'QA'), ('Diyala', 'DI'), ('Duhok', 'DA'), ('Erbil', 'AR'), ('Halabja', '—'), ('Karbala', 'KA'), ('Kirkuk', 'KI'), ('Maysan', 'MA'), ('Muthanna', 'MU'), ('Najaf', 'NA'), ('Nineveh', 'NI'), ('Saladin', 'SD'), ('Sulaymaniyah', 'SU'), ('Wasit', 'WA')], max_length=20, null=True),
        ),
    ]
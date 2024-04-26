# Generated by Django 2.2.16 on 2021-06-30 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0035_auto_20210223_1557'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='courseenrollment',
            options={},
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='level_of_education',
            field=models.CharField(blank=True, choices=[('p', 'PhD'), ('m', "Master's degree"), ('hd', 'High Diploma'), ('b', "Bachelor's degree"), ('a', 'Diploma'), ('hs', 'High School'), ('jhs', 'Intermediate School'), ('el', 'Primary School'), ('pc', 'Professional Certificate'), ('none', 'No Certificates'), ('other', 'Other education')], db_index=True, max_length=6, null=True),
        ),
    ]
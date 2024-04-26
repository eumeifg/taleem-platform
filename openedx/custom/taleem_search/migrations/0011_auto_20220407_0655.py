# Generated by Django 2.2.16 on 2022-04-07 03:55

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0023_auto_20201216_0753'),
        ('taleem_search', '0010_auto_20220405_1452'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursefilters',
            name='course',
            field=models.ForeignKey(default=None, limit_choices_to=models.Q(('is_timed_exam', 0), models.Q(('end_date__isnull', True), ('end_date__gt', datetime.datetime(2022, 4, 7, 3, 55, 7, 914540, tzinfo=utc)), _connector='OR')), null=True, on_delete=django.db.models.deletion.CASCADE, related_name='filters', to='course_overviews.CourseOverview'),
        ),
        migrations.CreateModel(
            name='AdvertisedCourse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course', models.OneToOneField(default=None, limit_choices_to=models.Q(('is_timed_exam', 0), models.Q(('end_date__isnull', True), ('end_date__gt', datetime.datetime(2022, 4, 7, 3, 55, 7, 913653, tzinfo=utc)), _connector='OR')), null=True, on_delete=django.db.models.deletion.CASCADE, related_name='advertised', to='course_overviews.CourseOverview')),
            ],
            options={
                'verbose_name_plural': 'Advertised Courses',
                'ordering': ('id',),
                'verbose_name': 'Advertised Course',
            },
        ),
    ]
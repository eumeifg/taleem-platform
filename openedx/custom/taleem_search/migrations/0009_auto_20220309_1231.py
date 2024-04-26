# Generated by Django 2.2.16 on 2022-03-09 09:31

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('taleem_search', '0008_auto_20220307_1518'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursefilters',
            name='course',
            field=models.ForeignKey(default=None, limit_choices_to=models.Q(('is_timed_exam', 0), models.Q(('end_date__isnull', True), ('end_date__gt', datetime.datetime(2022, 3, 9, 9, 31, 39, 287110, tzinfo=utc)), _connector='OR')), null=True, on_delete=django.db.models.deletion.CASCADE, related_name='filters', to='course_overviews.CourseOverview'),
        ),
        migrations.AlterField(
            model_name='examfilters',
            name='exam',
            field=models.ForeignKey(default=None, limit_choices_to={'exam_type': 'Public'}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='filters', to='timed_exam.TimedExam'),
        ),
    ]

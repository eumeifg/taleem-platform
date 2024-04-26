# Generated by Django 2.2.16 on 2022-03-07 12:15

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('timed_exam', '0028_timedexamextras'),
        ('taleem_search', '0006_add_live_course_filter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursefilters',
            name='course',
            field=models.ForeignKey(default=None, limit_choices_to=models.Q(('is_timed_exam', 0), models.Q(('end_date__isnull', True), ('end_date__gt', datetime.datetime(2022, 3, 7, 12, 14, 53, 163072, tzinfo=utc)), _connector='OR')), null=True, on_delete=django.db.models.deletion.CASCADE, related_name='filters', to='course_overviews.CourseOverview'),
        ),
        migrations.CreateModel(
            name='ExamFilters',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exam', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='filters', to='timed_exam.TimedExam')),
                ('filter_value', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_filters', to='taleem_search.FilterCategoryValue')),
            ],
            options={
                'verbose_name_plural': 'Exam Filters',
                'verbose_name': 'Exam Filter',
                'ordering': ('id',),
            },
        ),
    ]

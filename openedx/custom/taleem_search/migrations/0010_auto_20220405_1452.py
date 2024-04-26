# Generated by Django 2.2.16 on 2022-04-05 11:52

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('taleem_search', '0009_auto_20220309_1231'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='filtercategory',
            options={'ordering': ('-weightage',), 'verbose_name': 'Filter Category', 'verbose_name_plural': 'Filter Categories'},
        ),
        migrations.AddField(
            model_name='filtercategory',
            name='web_only',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='coursefilters',
            name='course',
            field=models.ForeignKey(default=None, limit_choices_to=models.Q(('is_timed_exam', 0), models.Q(('end_date__isnull', True), ('end_date__gt', datetime.datetime(2022, 4, 5, 11, 52, 20, 2516, tzinfo=utc)), _connector='OR')), null=True, on_delete=django.db.models.deletion.CASCADE, related_name='filters', to='course_overviews.CourseOverview'),
        ),
    ]
# Generated by Django 2.2.16 on 2021-12-10 19:09

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('timed_exam', '0020_timedexamalarms'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimedExamAlarmConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('is_active', models.BooleanField(default=True, help_text='Is this configuration active?')),
                ('alarm_time', models.IntegerField(validators=[django.core.validators.MinValueValidator(5), django.core.validators.MaxValueValidator(60)])),
                ('user', models.ForeignKey(help_text='User creating timed exam configuration.', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Timed Exam Alarm Configurations',
                'verbose_name': 'Timed Exam Alarm Configuration',
                'ordering': ['-is_active', 'alarm_time'],
            },
        ),
    ]

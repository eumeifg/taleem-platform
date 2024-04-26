# Generated by Django 2.2.16 on 2021-12-07 05:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('timed_exam', '0018_add_student_attempt'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OfflineExamStudentAttempt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('started_at', models.DateTimeField(null=True)),
                ('completed_at', models.DateTimeField(null=True)),
                ('attempt_code', models.CharField(db_index=True, max_length=255, null=True)),
                ('external_id', models.CharField(db_index=True, max_length=255, null=True)),
                ('status', models.CharField(max_length=64)),
                ('timed_exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='timed_exam.TimedExam')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'offline exam attempt',
                'unique_together': {('user', 'timed_exam')},
                'db_table': 'offline_exam_attempts',
            },
        ),
    ]

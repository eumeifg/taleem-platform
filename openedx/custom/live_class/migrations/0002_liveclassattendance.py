# Generated by Django 2.2.16 on 2021-05-24 07:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('live_class', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LiveClassAttendance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('joined_at', models.DateTimeField()),
                ('left_at', models.DateTimeField()),
                ('live_class', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='live_class.LiveClass')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_attendance', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Live Class Attendances',
                'verbose_name': 'Live Class Attendance',
            },
        ),
    ]

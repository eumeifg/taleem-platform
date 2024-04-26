# Generated by Django 2.2.16 on 2022-06-14 21:40

from django.db import migrations
import uuid


def gen_uuid_hex(apps, schema_editor):
    course_overview_model = apps.get_model('course_overviews', 'CourseOverview')
    for row in course_overview_model.objects.all():
        row.appstore_id = uuid.uuid4().hex
        row.save(update_fields=['appstore_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0024_auto_20220615_0038'),
    ]

    operations = [
        migrations.RunPython(gen_uuid_hex, reverse_code=migrations.RunPython.noop),
    ]
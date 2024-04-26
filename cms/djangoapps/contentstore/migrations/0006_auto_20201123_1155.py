# Generated by Django 2.2.17 on 2020-11-23 11:55

from django.db import migrations
from cms.djangoapps.contentstore.constants import TALEEM_ADMIN_GROUP


def add_taleem_admin_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name=TALEEM_ADMIN_GROUP)


def delete_taleem_admin_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name=TALEEM_ADMIN_GROUP).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contentstore', '0004_remove_push_notification_configmodel_table'),
    ]

    operations = [
        migrations.RunPython(add_taleem_admin_group, delete_taleem_admin_group)
    ]

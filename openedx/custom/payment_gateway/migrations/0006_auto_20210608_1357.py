# Generated by Django 2.2.16 on 2021-06-08 10:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payment_gateway', '0005_auto_20210416_1249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voucherusage',
            name='course',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='voucher_usages', to='course_overviews.CourseOverview'),
        ),
    ]

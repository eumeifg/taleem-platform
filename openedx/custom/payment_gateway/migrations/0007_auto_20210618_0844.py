# Generated by Django 2.2.16 on 2021-06-18 05:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payment_gateway', '0006_auto_20210608_1357'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voucherusage',
            name='course',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='voucher_usages', to='course_overviews.CourseOverview'),
        ),
    ]

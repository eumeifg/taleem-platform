# Generated by Django 2.2.16 on 2021-08-26 07:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taleem_organization', '0002_taleem_organization_verbose_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='poster',
            field=models.ImageField(blank=True, null=True, upload_to='subjects'),
        ),
        migrations.AddField(
            model_name='taleemorganization',
            name='poster',
            field=models.ImageField(blank=True, null=True, upload_to='organizations'),
        ),
    ]
# Generated by Django 2.2.16 on 2021-06-17 07:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('taleem_search', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='filtercategoryvalue',
            unique_together={('filter_category', 'value')},
        ),
    ]
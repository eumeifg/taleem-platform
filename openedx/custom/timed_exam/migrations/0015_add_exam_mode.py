# Generated by Django 2.2.16 on 2021-12-02 07:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timed_exam', '0014_auto_20211124_1734'),
    ]

    operations = [
        migrations.AddField(
            model_name='timedexam',
            name='mode',
            field=models.CharField(choices=[('ON', 'متصل'), ('OF', 'وضع غير متصل بالشبكة')], default='ON', max_length=2, verbose_name='طريقة الفحص'),
        ),
    ]

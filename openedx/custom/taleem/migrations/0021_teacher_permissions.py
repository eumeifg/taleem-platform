# Generated by Django 2.2.16 on 2022-10-25 04:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taleem', '0020_add_android_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='ta3leemuserprofile',
            name='can_answer_discussion',
            field=models.BooleanField(default=False, help_text='Can answer discussion questions?'),
        ),
        migrations.AddField(
            model_name='ta3leemuserprofile',
            name='can_create_course',
            field=models.BooleanField(default=False, help_text='Can create course?'),
        ),
        migrations.AddField(
            model_name='ta3leemuserprofile',
            name='can_create_exam',
            field=models.BooleanField(default=False, help_text='Can create exam?'),
        ),
        migrations.AddField(
            model_name='ta3leemuserprofile',
            name='can_use_chat',
            field=models.BooleanField(default=False, help_text='Can use chat feature?'),
        ),
    ]
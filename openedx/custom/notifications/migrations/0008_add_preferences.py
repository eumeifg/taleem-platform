# Generated by Django 2.2.16 on 2022-12-16 05:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notifications', '0007_add_mute_post'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receive_on', models.CharField(choices=[('wb', 'Web'), ('mb', 'Mobile'), ('bt', 'كلاهما'), ('nw', 'Nowhere')], db_index=True, default='bt', max_length=2)),
                ('added_discussion_post', models.BooleanField(default=False, verbose_name='Notify when students adds new discussion post')),
                ('added_discussion_comment', models.BooleanField(default=False, verbose_name='Notify when students adds new discussion comment')),
                ('asked_question', models.BooleanField(default=True, verbose_name='Notify when students asks question')),
                ('replied_on_question', models.BooleanField(default=False, verbose_name='Notify when students replies on question')),
                ('asked_private_question', models.BooleanField(default=True, verbose_name='Notify when students asks private question')),
                ('replied_on_private_question', models.BooleanField(default=False, verbose_name='Notify when students replies on private question')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

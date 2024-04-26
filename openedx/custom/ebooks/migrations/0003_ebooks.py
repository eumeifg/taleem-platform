# Generated by Django 2.2.16 on 2021-09-13 10:14

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import openedx.custom.ebooks.models
import taggit.managers
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('taleem', '0009_adding_grade'),
        ('taggit', '0003_taggeditem_add_unique_index'),
        ('ebooks', '0002_ebooks_category_Arabic_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='EBook',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('cover', models.ImageField(blank=True, null=True, upload_to='ebooks/cover', verbose_name='Cover Image')),
                ('pages', models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Number of pages')),
                ('pdf', models.FileField(max_length=255, upload_to=openedx.custom.ebooks.models.ebook_directory_path)),
                ('access_type', models.CharField(choices=[('PB', 'Open for all'), ('PV', 'Open for my organization')], default='PB', max_length=2, verbose_name='Access Type')),
                ('published', models.BooleanField(default=False, verbose_name='Publish ?')),
                ('published_on', models.DateTimeField(blank=True, null=True, verbose_name='Published On')),
                ('author', models.ForeignKey(limit_choices_to={'user_type': 'teacher'}, on_delete=django.db.models.deletion.CASCADE, related_name='ebooks', to='taleem.Ta3leemUserProfile')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ebooks', to='ebooks.EBookCategory', verbose_name='Category')),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags')),
            ],
            options={
                'verbose_name_plural': 'eBooks',
                'verbose_name': 'eBook',
            },
        ),
    ]

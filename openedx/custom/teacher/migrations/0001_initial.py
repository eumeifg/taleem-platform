# Generated by Django 2.2.16 on 2022-03-15 04:01

import django.core.validators
from django.db import migrations, models
import django.utils.timezone
import django_countries.fields
import model_utils.fields
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccessRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('first_name', models.CharField(max_length=255, verbose_name='First Name')),
                ('last_name', models.CharField(max_length=255, verbose_name='Last Name')),
                ('country', django_countries.fields.CountryField(max_length=2, verbose_name='Country')),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None, verbose_name='Phone Number')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('speciality', models.CharField(max_length=255, verbose_name='Speciality')),
                ('qualifications', models.CharField(max_length=255, verbose_name='Qualifications')),
                ('course_title', models.CharField(blank=True, max_length=255, null=True, verbose_name='Course Title')),
                ('profile_photo', models.ImageField(upload_to='teachers/photos', verbose_name='Profile Photo')),
                ('cv_file', models.FileField(upload_to='teachers/CV', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])])),
                ('stage', models.CharField(choices=[('ur', 'Under Review'), ('ap', 'Approved'), ('de', 'Declined')], db_index=True, default='ur', max_length=2)),
            ],
            options={
                'ordering': ('-created',),
                'verbose_name_plural': 'Access Requests',
                'verbose_name': 'Access Request',
            },
        ),
    ]

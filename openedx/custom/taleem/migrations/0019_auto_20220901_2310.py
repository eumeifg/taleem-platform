# Generated by Django 2.2.16 on 2022-09-01 20:10

from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('taleem', '0018_ta3leemuserprofile_is_test_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='ta3leemuserprofile',
            name='category_selection',
            field=models.CharField(choices=[('NA', 'Not Applicable'), ('AB', 'Arabic Based'), ('EB', 'English Based'), ('AS', 'Applicational Studies'), ('BS', 'Biological Studies')], default='NA', max_length=32),
        ),
        migrations.AddField(
            model_name='ta3leemuserprofile',
            name='sponsor_mobile_number',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region=None),
        ),
    ]
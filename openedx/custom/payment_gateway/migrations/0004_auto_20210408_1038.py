# Generated by Django 2.2.16 on 2021-04-08 07:38

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment_gateway', '0003_voucher_voucherusage'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='voucher',
            options={'verbose_name': 'Voucher', 'verbose_name_plural': 'Vouchers'},
        ),
        migrations.AlterModelOptions(
            name='voucherusage',
            options={'verbose_name': 'Voucher Usage', 'verbose_name_plural': 'Voucher Usages'},
        ),
        migrations.AlterField(
            model_name='courseprice',
            name='price',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12, verbose_name='Course Price'),
        ),
    ]

# Generated by Django 4.1.1 on 2023-05-17 10:27

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0012_alter_indexform_date_zap'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indexform',
            name='DATE_ZAP',
            field=models.DateField(default=datetime.datetime(2023, 5, 1, 10, 27, 13, 506106, tzinfo=datetime.timezone.utc), max_length=10, verbose_name='DATE_ZAP'),
        ),
    ]

# Generated by Django 4.1.1 on 2023-06-20 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0019_alter_indexform_date_zap_alter_indexform_body'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indexform',
            name='home',
            field=models.CharField(max_length=100, verbose_name='Дом'),
        ),
    ]
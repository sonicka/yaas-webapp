# Generated by Django 2.0.1 on 2018-01-21 12:10

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('yaas', '0020_auto_20180121_0312'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auction',
            name='title',
            field=models.CharField(default=None, max_length=24, validators=[django.core.validators.ProhibitNullCharactersValidator()]),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-10 11:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('yaas', '0009_auto_20171009_2245'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auction',
            name='deadline',
            field=models.DateField(blank=True, null=True),
        ),
    ]

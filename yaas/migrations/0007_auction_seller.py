# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-09 13:55
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('yaas', '0006_remove_auction_seller'),
    ]

    operations = [
        migrations.AddField(
            model_name='auction',
            name='seller',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]

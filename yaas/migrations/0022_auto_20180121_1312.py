# Generated by Django 2.0.1 on 2018-01-21 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('yaas', '0021_auto_20180121_1310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auction',
            name='title',
            field=models.CharField(default='', max_length=24),
        ),
    ]

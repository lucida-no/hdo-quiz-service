# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-07 17:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0015_auto_20170716_2133'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='manuscript',
            name='is_default',
        ),
        migrations.AddField(
            model_name='manuscript',
            name='default',
            field=models.CharField(choices=[('default', 'Default'), ('default_vg', 'Voter guide'), ('none', 'None')], default='none', max_length=254),
        ),
    ]
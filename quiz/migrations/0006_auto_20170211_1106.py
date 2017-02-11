# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-02-11 11:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0005_auto_20170211_1059'),
    ]

    operations = [
        migrations.CreateModel(
            name='ManuscriptImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('url', models.URLField()),
                ('image', models.ImageField(upload_to='')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='manuscriptitem',
            name='type',
            field=models.CharField(choices=[('button', 'Button'), ('promises', 'Promises'), ('text', 'Text'), ('url', 'URL')], default='text', max_length=100),
        ),
    ]

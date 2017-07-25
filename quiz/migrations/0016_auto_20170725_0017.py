# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-25 00:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0015_auto_20170716_2133'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manuscript',
            name='hdo_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='manuscripts', to='quiz.HdoCategory'),
        ),
        migrations.AlterField(
            model_name='manuscriptitem',
            name='type',
            field=models.CharField(choices=[('text', 'Text'), ('quick_reply', 'Quick reply'), ('url', 'URL'), ('quiz_result', 'Quiz: Show result'), ('quiz_q_promises_checked', 'Quiz: Show checked promise questions'), ('quiz_q_party_select', 'Quiz: Show which party promised what questions'), ('quiz_q_party_bool', 'Quiz: Show did party x promise y questions'), ('vg_result', 'Voter guide: Show result'), ('vg_categories', 'Voter guide: Show category select'), ('vg_questions', 'Voter guide: Show questions'), ('vg_show_next', 'Voter guide: Show results or continue')], default='text', max_length=100),
        ),
        migrations.AlterField(
            model_name='voterguideanswer',
            name='voter_guide_alternative',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='answers', to='quiz.VoterGuideAlternative'),
        ),
    ]
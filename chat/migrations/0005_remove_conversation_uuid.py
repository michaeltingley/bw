# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-18 05:29
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_conversation_uuid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='conversation',
            name='uuid',
        ),
    ]

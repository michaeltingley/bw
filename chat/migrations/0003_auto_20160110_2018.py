# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-10 20:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_conversation_participants'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]

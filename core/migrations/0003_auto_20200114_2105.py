# Generated by Django 2.2.6 on 2020-01-14 20:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20200114_2102'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='DataFile',
            new_name='DataFileInfo',
        ),
        migrations.RenameModel(
            old_name='ProfileFile',
            new_name='ProfileInfo',
        ),
    ]
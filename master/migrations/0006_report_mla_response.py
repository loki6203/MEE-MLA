# Generated by Django 4.2.4 on 2023-09-06 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0005_uservote'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='mla_response',
            field=models.CharField(max_length=150, null=True),
        ),
    ]
# Generated by Django 4.2.4 on 2023-09-19 16:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0004_voter_age_voter_gender_voter_remarks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voter',
            name='party',
            field=models.CharField(max_length=50, null=True),
        ),
    ]

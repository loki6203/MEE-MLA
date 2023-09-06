# Generated by Django 4.2.4 on 2023-09-05 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0002_constituency'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='image',
            field=models.FileField(blank=True, null=True, upload_to='uploads/reports'),
        ),
        migrations.AlterField(
            model_name='report',
            name='status',
            field=models.CharField(choices=[('failed', 'Failed'), ('pending', 'Pending'), ('solved', 'Solved')], default='pending', max_length=20),
        ),
    ]
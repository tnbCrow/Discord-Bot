# Generated by Django 3.2.6 on 2021-08-18 03:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('escrow', '0003_auto_20210817_1614'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='withdrawl_address',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]

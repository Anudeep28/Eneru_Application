# Generated by Django 5.0.1 on 2024-01-29 21:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0003_category_remove_chitfund_user_client_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='client.userprofile'),
        ),
    ]

# Generated by Django 5.0.1 on 2025-03-04 09:36

import pgvector.django.vector
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('financial_analyzer', '0003_documentchunk_embedding'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentchunk',
            name='embedding',
            field=pgvector.django.vector.VectorField(blank=True, dimensions=384, null=True),
        ),
    ]

# Generated by Django 5.0.1 on 2025-02-16 23:15

import django.contrib.postgres.fields
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FinancialAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500)),
                ('summary', models.TextField()),
                ('key_metrics', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=500), blank=True, help_text='Important financial metrics mentioned in the content', size=None)),
                ('recommendations', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1000), blank=True, help_text='Key takeaways and recommendations from the analysis', size=None)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Financial Analysis',
                'verbose_name_plural': 'Financial Analyses',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WebsiteContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(max_length=2000)),
                ('title', models.CharField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Website Content',
                'verbose_name_plural': 'Website Contents',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DialogueMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('speaker', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('sequence', models.IntegerField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('analysis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dialogue', to='financial_analyzer.financialanalysis')),
            ],
            options={
                'ordering': ['sequence'],
            },
        ),
        migrations.AddField(
            model_name='financialanalysis',
            name='website',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='financial_analyses', to='financial_analyzer.websitecontent'),
        ),
        migrations.CreateModel(
            name='ContentChunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('sequence', models.IntegerField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('website', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='financial_analyzer.websitecontent')),
            ],
            options={
                'ordering': ['sequence'],
            },
        ),
    ]

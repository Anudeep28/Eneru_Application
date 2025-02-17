from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone

# Create your models here.

class WebsiteContent(models.Model):
    url = models.URLField(max_length=2000)
    title = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.url})"

    class Meta:
        verbose_name = "Website Content"
        verbose_name_plural = "Website Contents"
        ordering = ['-created_at']

class ContentChunk(models.Model):
    website = models.ForeignKey(WebsiteContent, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()
    sequence = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['sequence']

    def __str__(self):
        return f"Chunk {self.sequence} for {self.website.title}"

class FinancialAnalysis(models.Model):
    website = models.ForeignKey(WebsiteContent, on_delete=models.CASCADE, related_name='financial_analyses')
    title = models.CharField(max_length=500)
    summary = models.TextField()
    key_metrics = ArrayField(
        models.CharField(max_length=500),
        blank=True,
        help_text="Important financial metrics mentioned in the content"
    )
    recommendations = ArrayField(
        models.CharField(max_length=1000),
        blank=True,
        help_text="Key takeaways and recommendations from the analysis"
    )
    created_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Financial Analysis: {self.title}"

    class Meta:
        verbose_name = "Financial Analysis"
        verbose_name_plural = "Financial Analyses"
        ordering = ['-created_at']

    def get_metrics_count(self):
        return len(self.key_metrics)

    def get_recommendations_count(self):
        return len(self.recommendations)

class DialogueMessage(models.Model):
    analysis = models.ForeignKey(FinancialAnalysis, on_delete=models.CASCADE, related_name='dialogue')
    speaker = models.CharField(max_length=200)
    message = models.TextField()
    sequence = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['sequence']

    def __str__(self):
        return f"{self.speaker} - Message {self.sequence}"

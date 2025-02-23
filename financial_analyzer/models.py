import uuid
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone  # Import timezone
from pgvector.django import VectorField
from django.conf import settings

class WebsiteData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='website_data')
    url = models.URLField(unique=True)
    title = models.CharField(max_length=500, blank=True)
    company = models.CharField(max_length=255)
    year = models.IntegerField()
    quarter = models.CharField(max_length=2)
    extracted_content = models.JSONField()
    fit_markdown = models.TextField()
    # vector_embeddings = VectorField(dimensions=768)  # Adjust dimensions as needed
    created_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company} - {self.year} Q{self.quarter}"

    class Meta:
        ordering = ['-created_at']

class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    website = models.ForeignKey(WebsiteData, on_delete=models.CASCADE, related_name='chunks')
    sequence = models.PositiveIntegerField(help_text="Chunk position in document")
    content = models.TextField()
    embedding = VectorField(dimensions=768, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['sequence']
        indexes = [
            models.Index(fields=['website', 'sequence']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Chunk {self.sequence} of {self.website}"

class UserQuery(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    query = models.TextField()
    response = models.TextField()
    website = models.ForeignKey(WebsiteData, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Query by {self.user} on {self.created_at}"
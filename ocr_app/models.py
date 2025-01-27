from django.db import models
from django.utils import timezone
from django.conf import settings

# Create your models here.

class OCRDocument(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    document = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(default=timezone.now)
    processed_text = models.TextField(blank=True)
    markdown_output = models.TextField(blank=True)  # Stores JSON structure
    raw_markdown = models.TextField(blank=True)  # Stores raw markdown from LLM
    
    def __str__(self):
        return f"Document uploaded by {self.user.username} at {self.uploaded_at}"

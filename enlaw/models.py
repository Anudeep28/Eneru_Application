from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import json

User = get_user_model()

class TemplateVariable(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    validation_regex = models.CharField(max_length=255, blank=True)
    required = models.BooleanField(default=False)
    default_value = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.name

class Template(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    content = models.TextField()
    variables = models.ManyToManyField(TemplateVariable)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def validate_variables(self, variable_values):
        """Validate the provided variable values against template variables"""
        errors = {}
        for var in self.variables.all():
            value = variable_values.get(var.name)
            if var.required and not value:
                errors[var.name] = "This field is required"
            elif value and var.validation_regex:
                import re
                if not re.match(var.validation_regex, value):
                    errors[var.name] = "Invalid format"
        return errors

class Document(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('final', 'Final'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    template_source = models.CharField(max_length=255)  # Path for static templates or ID for DB templates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    variable_values = models.JSONField(default=dict)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Validate variable values before saving
        if self.template_source.isdigit():
            template = Template.objects.get(id=int(self.template_source))
            errors = template.validate_variables(self.variable_values)
            if errors:
                raise ValidationError(errors)
        super().save(*args, **kwargs)

    def to_pdf(self):
        """Convert document content to PDF format"""
        # PDF conversion logic will be implemented in the view
        pass

from django.contrib import admin
from .models import Template, Document

# Register your models here.

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'content')
    ordering = ('-created_at',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'template_source', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'content')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from .models import Template, Document, TemplateVariable
import json
import os
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
import re

# Create your views here.

class TemplateListView(LoginRequiredMixin, ListView):
    model = Template
    template_name = 'enlaw/template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        queryset = Template.objects.filter(is_public=True) | Template.objects.filter(created_by=self.request.user)
        search_query = self.request.GET.get('search', '')
        category = self.request.GET.get('category', '')
        
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.distinct()

class TemplateDetailView(LoginRequiredMixin, DetailView):
    model = Template
    template_name = 'enlaw/template_preview.html'
    context_object_name = 'template'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['variables'] = self.object.variables.all()
        return context

@login_required
def edit_document(request, template_id=None, document_id=None):
    context = {}
    
    if document_id:
        document = get_object_or_404(Document, id=document_id, created_by=request.user)
        context['document'] = document
        context['template'] = Template.objects.get(id=document.template_source) if document.template_source.isdigit() else None
    elif template_id:
        template = get_object_or_404(Template, id=template_id)
        context['template'] = template
        context['variables'] = template.variables.all()
    
    if request.method == 'POST':
        try:
            title = request.POST.get('document_title', 'Untitled Document')
            content = request.POST.get('content', '')
            variable_values = {}
            
            # Collect variable values from form
            for field_name, value in request.POST.items():
                if field_name.startswith('var_'):
                    variable_name = field_name[4:]  # Remove 'var_' prefix
                    variable_values[variable_name] = value
            
            if document_id:
                document.title = title
                document.content = content
                document.variable_values = variable_values
                document.save()
            else:
                document = Document.objects.create(
                    title=title,
                    content=content,
                    template_source=template_id,
                    created_by=request.user,
                    variable_values=variable_values
                )
            
            return redirect('enlaw:document_detail', document_id=document.id)
            
        except ValidationError as e:
            context['errors'] = e.message_dict
    
    return render(request, 'enlaw/document_editor.html', context)

@login_required
@require_http_methods(["POST"])
def save_document_progress(request):
    try:
        data = json.loads(request.body)
        document_id = data.get('document_id')
        
        if document_id:
            document = get_object_or_404(Document, id=document_id, created_by=request.user)
        else:
            document = Document(created_by=request.user)
        
        document.title = data.get('title', document.title)
        document.content = data.get('content', '')
        document.variable_values = data.get('fields', {})
        document.status = 'draft'
        document.save()
        
        return JsonResponse({
            'status': 'success',
            'document_id': document.id
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
def export_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, created_by=request.user)
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{document.title}.pdf"'
    
    # Create the PDF object using ReportLab
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30
    )
    
    # Create the PDF content
    elements = []
    
    # Add title
    elements.append(Paragraph(document.title, title_style))
    elements.append(Spacer(1, 12))
    
    # Add content
    content_style = styles["Normal"]
    
    # Process the content to handle HTML-like formatting
    content = document.content
    # Convert basic HTML to ReportLab-friendly format
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'<[^>]+>', '', content)  # Remove other HTML tags
    
    elements.append(Paragraph(content, content_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and return the PDF file
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response

@login_required
def delete_document(request, document_id):
    if request.method == 'POST':
        document = get_object_or_404(Document, id=document_id, created_by=request.user)
        document.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=405)

def list_static_templates(request):
    # Define the static templates directory, adjust the path if needed
    templates_dir = os.path.join(settings.BASE_DIR, 'static', 'enlaw', 'templates')
    templates = []
    if os.path.exists(templates_dir):
        for filename in os.listdir(templates_dir):
            if filename.endswith('.html'):
                templates.append({'title': filename, 'path': filename})
    return render(request, 'enlaw/template_list.html', {'templates': templates})

def edit_static_template(request, template_path):
    templates_dir = os.path.join(settings.BASE_DIR, 'static', 'enlaw', 'templates')
    filepath = os.path.join(templates_dir, template_path)

    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            content = file.read()
    else:
        content = 'File not found'

    template = {
        'id': '',
        'title': template_path,
        'category': 'Static',
        'content': content
    }
    return render(request, 'enlaw/template_preview.html', {'template': template})

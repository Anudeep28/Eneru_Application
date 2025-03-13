from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.forms import modelform_factory
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh
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
from django.contrib import messages

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
def edit_document(request, template_id=None, template_path=None, document_id=None):
    if template_path:
        # Handle static template
        # Clean up template path and ensure it ends with .json
        template_path = template_path.replace('.html', '.json')
        if not template_path.endswith('.json'):
            template_path += '.json'
            
        # Extract the filename from the path if it includes directories
        template_filename = os.path.basename(template_path)
        template_file_path = os.path.join(settings.BASE_DIR, 'enlaw', 'static', 'enlaw', 'templates', template_filename)
        print(f"Loading template from: {template_file_path}")  # Debug print
        
        try:
            with open(template_file_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                print(f"Template data loaded: {json.dumps(template_data, indent=2)}")  # Debug print
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading template: {str(e)}")  # Debug print
            raise Http404("Template not found or invalid")
        
        if request.method == 'POST':
            # Create a new document from the static template
            variable_values = {}
            for field_name, value in request.POST.items():
                if field_name.startswith('var_'):
                    variable_name = field_name[4:]  # Remove 'var_' prefix
                    variable_values[variable_name] = value
            
            document = Document.objects.create(
                title=request.POST.get('document_title', template_data.get('title', 'Untitled')),
                content=template_data.get('content', ''),
                template_source=template_file_path,
                created_by=request.user,
                variable_values=variable_values,
                status='draft'
            )
            
            return redirect('enlaw:edit_document', document_id=document.id)
        
        context = {
            'template': template_data,
            'document_id': document_id,
            'template_json': json.dumps(template_data)
        }
        print(f"Context data: {json.dumps(context, indent=2)}")  # Debug print
        return render(request, 'enlaw/edit_document.html', context)
    
    elif template_id:
        # Handle database template
        template = get_object_or_404(Template, pk=template_id)
        document = None
        
        if document_id:
            document = get_object_or_404(Document, pk=document_id)
            if document.created_by != request.user:
                raise Http404("Document not found")
        
        # Create template_json for database template
        template_json = {
            'title': template.title,
            'content': template.content,
            'variables': {}
        }
        
        # Get template variables
        for variable in template.variables.all():
            template_json['variables'][variable.name] = {
                'label': variable.label or variable.name.replace('_', ' ').title(),
                'type': variable.field_type,
                'required': variable.required
            }
        
        context = {
            'template': template,
            'document': document,
            'document_id': document_id,
            'is_static': False,
            'template_json': json.dumps(template_json)
        }
        
        return render(request, 'enlaw/edit_document.html', context)
    
    else:
        raise Http404("No template specified")

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

@login_required
def dynamic_form_edit(request, template_id=None):
    """
    View for dynamically editing a form based on a template using HTMX.
    """
    template = get_object_or_404(Template, pk=template_id)
    template_variables = template.variables.all()
    
    # Create initial context with template information
    context = {
        'template': template,
        'variables': template_variables,
        'is_htmx': request.headers.get('HX-Request') == 'true'
    }
    
    if request.method == 'POST':
        # Process form submission
        variable_values = {}
        form_valid = True
        errors = {}
        
        for var in template_variables:
            value = request.POST.get(f'var_{var.name}')
            if var.required and not value:
                form_valid = False
                errors[var.name] = 'This field is required'
            elif var.validation_regex and value:
                import re
                if not re.match(var.validation_regex, value):
                    form_valid = False
                    errors[var.name] = 'Invalid format'
            
            variable_values[var.name] = value
        
        if not form_valid:
            context['errors'] = errors
            return render(request, 'enlaw/dynamic_form.html', context)
        
        # Create new document from template
        document = Document.objects.create(
            title=request.POST.get('document_title', template.title),
            content=template.content,
            template_source=str(template.id),
            created_by=request.user,
            variable_values=variable_values,
            status='draft'
        )
        
        # If HTMX request, return partial response
        if context['is_htmx']:
            return HttpResponse(
                f'''<div hx-swap-oob="true" id="form-status">
                    <div class="alert alert-success">{template.success_message or "Document created successfully!"}</div>
                </div>'''
            )
        
        # Otherwise redirect to document edit page or success URL
        if template.success_url:
            return redirect(template.success_url)
        return redirect('enlaw:edit_document', document_id=document.id)
    
    return render(request, 'enlaw/dynamic_form.html', context)

@login_required
def update_field(request, template_id, field_name):
    """
    HTMX endpoint for updating a single field in the form.
    """
    template = get_object_or_404(Template, pk=template_id)
    field = get_object_or_404(TemplateVariable, name=field_name, template=template)
    
    value = request.POST.get(f'var_{field_name}')
    is_valid = True
    error_message = ''
    
    # Validate field if required
    if field.required and not value:
        is_valid = False
        error_message = 'This field is required'
    elif field.validation_regex and value:
        import re
        if not re.match(field.validation_regex, value):
            is_valid = False
            error_message = 'Invalid format'
    
    # Return appropriate response based on validation
    if is_valid:
        return HttpResponse(
            f'''<div class="field-status valid" id="status-{field_name}">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-check-circle" viewBox="0 0 16 16">
                    <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                    <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"/>
                </svg>
            </div>'''
        )
    else:
        return HttpResponse(
            f'''<div class="field-status invalid" id="status-{field_name}">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-exclamation-circle" viewBox="0 0 16 16">
                    <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                    <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"/>
                </svg>
                <span class="error-message">{error_message}</span>
            </div>'''
        )

@login_required
def simple_form_edit(request, template_path=None):
    """
    A simplified form editing view that directly renders a form for template variables.
    """
    # Clean up template path and ensure it ends with .json
    template_path = template_path.replace('.html', '.json')
    if not template_path.endswith('.json'):
        template_path += '.json'
        
    # Extract the filename from the path if it includes directories
    template_filename = os.path.basename(template_path)
    templates_dir = os.path.join(settings.BASE_DIR, 'enlaw', 'static', 'enlaw', 'templates')
    filepath = os.path.join(templates_dir, template_filename)
    
    print(f"Loading template from: {filepath}")  # Debug print
    
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Template file not found: {template_path}")
            
        with open(filepath, 'r', encoding='utf-8') as file:
            template_data = json.load(file)
            
        if request.method == 'POST':
            # Process form submission
            variable_values = {}
            for field_name, value in request.POST.items():
                if field_name.startswith('var_'):
                    variable_name = field_name[4:]  # Remove 'var_' prefix
                    variable_values[variable_name] = value
            
            # Create a new document
            document = Document.objects.create(
                title=request.POST.get('document_title', template_data.get('title', 'Untitled')),
                content=template_data.get('content', ''),
                template_source=filepath,
                created_by=request.user,
                variable_values=variable_values,
                status='draft'
            )
            
            messages.success(request, 'Document created successfully!')
            return redirect('enlaw:document_list')
            
        context = {
            'template': template_data,
            'document_id': None,
        }
        return render(request, 'enlaw/simple_form_edit.html', context)
        
    except Exception as e:
        print(f"Error loading template: {str(e)}")  # Debug print
        messages.error(request, f"Error loading template: {str(e)}")
        return redirect('enlaw:template_list')

def list_static_templates(request):
    # Define the static templates directory, adjust the path if needed
    templates_dir = os.path.join(settings.BASE_DIR, 'enlaw', 'static', 'enlaw', 'templates')
    templates = []
    
    # Get database templates
    db_templates = Template.objects.all()
    for template in db_templates:
        templates.append({
            'id': template.id,
            'title': template.title,
            'category': template.category,
            'path': '',
            'is_db_template': True
        })
    
    # Get static templates
    if os.path.exists(templates_dir):
        for filename in os.listdir(templates_dir):
            if filename.endswith('.json'):
                # Extract template name without extension
                template_name = os.path.splitext(filename)[0]
                # Read the JSON file to get the title
                try:
                    with open(os.path.join(templates_dir, filename), 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        title = template_data.get('title', template_name)
                        category = template_data.get('category', 'Legal')
                except (json.JSONDecodeError, FileNotFoundError):
                    title = template_name
                    category = 'Legal'
                
                templates.append({
                    'id': '',
                    'title': title,
                    'category': category,
                    'path': filename,
                    'is_db_template': False
                })
    
    # Get search parameters
    search_query = request.GET.get('search', '').lower()
    category_filter = request.GET.get('category', '')
    
    # Filter templates
    if search_query or category_filter:
        filtered_templates = []
        for template in templates:
            if (not search_query or search_query in template['title'].lower()) and \
               (not category_filter or category_filter == template['category']):
                filtered_templates.append(template)
        templates = filtered_templates
    
    # Get unique categories for filter dropdown
    categories = sorted(set(template['category'] for template in templates if template['category']))
    
    return render(request, 'enlaw/template_list.html', {
        'templates': templates,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter
    })

@login_required
def edit_static_template(request, template_path):
    # Clean up template path and ensure it ends with .json
    template_path = template_path.replace('.html', '.json')
    if not template_path.endswith('.json'):
        template_path += '.json'
        
    # Extract the filename from the path if it includes directories
    template_filename = os.path.basename(template_path)
    templates_dir = os.path.join(settings.BASE_DIR, 'enlaw', 'static', 'enlaw', 'templates')
    filepath = os.path.join(templates_dir, template_filename)
    
    print(f"Loading template from: {filepath}")  # Debug print
    
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Template file not found: {template_path}")
            
        with open(filepath, 'r', encoding='utf-8') as file:
            if filepath.endswith('.json'):
                try:
                    template_data = json.load(file)
                    template = {
                        'id': '',
                        'title': template_data.get('title', template_path),
                        'category': 'Static',
                        'content': template_data.get('content', ''),
                        'variables': template_data.get('variables', {})
                    }
                    # Keep the original template_data for JSON script
                    template_json = template_data
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON template file: {e}")
            else:
                content = file.read()
                # For HTML templates, we'll look for variables in the format {{variable_name}}
                variables = {}
                for match in re.finditer(r'\{\{\s*([^}]+)\s*\}\}', content):
                    var_name = match.group(1).strip()
                    variables[var_name] = {
                        'label': var_name.replace('_', ' ').title(),
                        'type': 'text',
                        'required': True
                    }
                
                template = {
                    'id': '',
                    'title': os.path.splitext(template_path)[0].replace('_', ' ').title(),
                    'category': 'Static',
                    'content': content,
                    'variables': variables
                }
                # Create template_json for HTML templates
                template_json = {
                    'title': template['title'],
                    'content': content,
                    'variables': variables
                }
        
        # Print the template_json for debugging
        print(f"Template JSON: {json.dumps(template_json, indent=2)}")
        
        context = {
            'template': template,
            'template_json': json.dumps(template_json),
            'document_id': request.GET.get('document_id', '')
        }
        return render(request, 'enlaw/edit_document.html', context)
        
    except Exception as e:
        print(f"Error loading template: {str(e)}")  # Debug print
        error_template = {
            'id': '',
            'title': 'Error Loading Template',
            'category': 'Static',
            'content': str(e),
            'variables': {}
        }
        error_template_json = {
            'title': 'Error Loading Template',
            'content': str(e),
            'variables': {}
        }
        return render(request, 'enlaw/edit_document.html', {
            'template': error_template,
            'template_json': json.dumps(error_template_json),
        })

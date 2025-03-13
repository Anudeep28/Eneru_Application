from django.urls import path
from . import views
from .views import list_static_templates

app_name = 'enlaw'

urlpatterns = [
    path('', list_static_templates, name='template_list'),
    path('template/<int:pk>/', views.TemplateDetailView.as_view(), name='template_preview'),
    path('edit/<int:template_id>/', views.edit_document, name='edit_document'),
    path('edit-static/<str:template_path>/', views.edit_static_template, name='edit_static_template'),
    path('simple-form/<str:template_path>/', views.simple_form_edit, name='simple_form_edit'),
    path('save/<int:document_id>/', views.save_document_progress, name='save_progress'),
    path('export/<int:document_id>/', views.export_document, name='export_document'),
    
    # Dynamic form editing with HTMX
    path('dynamic-form/<int:template_id>/', views.dynamic_form_edit, name='dynamic_form_edit'),
    path('update-field/<int:template_id>/<str:field_name>/', views.update_field, name='update_field'),
]

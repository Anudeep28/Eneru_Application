#from django.shortcuts import render, redirect
# class functions of django
from django.views.generic import TemplateView

class landing_page(TemplateView):
    # field name which Templateview understands
    # is template_name as below
    template_name = 'landing.html'
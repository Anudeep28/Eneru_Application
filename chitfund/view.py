#from django.shortcuts import render, redirect
# class functions of django
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView
from client.forms import LoginUserForm


class landing_page(TemplateView):
    # field name which Templateview understands
    # is template_name as below
    template_name = 'landing.html'


class CustomLoginView(LoginView):
    form_class = LoginUserForm

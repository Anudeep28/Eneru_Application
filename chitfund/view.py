#from django.shortcuts import render, redirect
# class functions of django
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView
from client.forms import ChitfundUserForm

class LandingPageView(TemplateView):
    template_name = "landing.html"


class CustomLoginView(LoginView):
    #form_class = LoginUserForm
    template_name = 'your_app/login.html'
    form_class = ChitfundUserForm

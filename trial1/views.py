from django.shortcuts import render, redirect
#from .models import Item, appoptions, User, Option
from .name_model import nameGen
#from .mixins import NameGenLoginRequiredMixin
#from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# User Creation Form is useful in grabbing all the information from html form tag
#from django.contrib.auth.forms import UserCreationForm
# To display messages to the user using Django built in forms
# from django.contrib import messages
# from django.views import generic
from django.http import HttpResponse
# initialized the LLM
# call the LLM function
llm = nameGen()


@login_required(login_url='login')
def NameGenerator(request):
    user = request.user
    if not user.is_authenticated or not user.is_namegen_user:
        return HttpResponse("""<h1>You have not subscribed for NameGen!!</h1>""")

    if request.method == 'GET':
        name_list = []
        #registered_option = appoptions.objects.get(owner = request.user)
        return render(request, template_name='trial1/NameGenerator.html',context={'name_list':name_list})
    if request.method == 'POST':
        #print(request.POST.get('submit'))
        if request.POST.get('submit') == 'Submit':

            # get the number input by user
            number = int(request.POST.get('number'))
            letter = request.POST.get('letter')
            name_list = llm.gen_name2(num=number,letter=letter)

            #print(name_list)
            return render(request, template_name='trial1/NameGenerator.html',context={'name_list':name_list})
        if request.POST.get('clear') == 'Clear':
            #print(request.POST.get('clear'))
            name_list = []
            return render(request, template_name='trial1/NameGenerator.html',context={'name_list':name_list})

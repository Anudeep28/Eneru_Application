from django.shortcuts import render, redirect
from django.views import generic
from .models import NameGenerator
from client.mixins import NamegenAccessMixin
from .name_model import nameGen
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages

llm = nameGen()


class NameGeneratorListView(NamegenAccessMixin, generic.ListView):
    template_name = "trial1/namegen_list.html"
    context_object_name = "namegen"

    def get_queryset(self):
        user = self.request.user
        return NameGenerator.objects.filter(user=user)


class NameGeneratorCreateView(NamegenAccessMixin, generic.CreateView):
    template_name = "trial1/namegen_create.html"
    model = NameGenerator
    fields = ['name']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return "/trial1"


class NameGeneratorView(NamegenAccessMixin, generic.View):
    template_name = "trial1/NameGenerator.html"

    def get(self, request):
        name_list = []
        return render(request, template_name=self.template_name, context={'name_list': name_list})

    def post(self, request):
        if request.POST.get('submit') == 'Submit':
            number = int(request.POST.get('number'))
            letter = request.POST.get('letter')
            name_list = llm.gen_name2(num=number, letter=letter)
            return render(request, template_name=self.template_name, context={'name_list': name_list})
        if request.POST.get('clear') == 'Clear':
            name_list = []
            return render(request, template_name=self.template_name, context={'name_list': name_list})

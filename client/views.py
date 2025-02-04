from typing import Any
from django.db.models.query import QuerySet
from django.forms.models import BaseModelForm
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.http import HttpResponse
from .models import User, ChitFund, Client, Category
from .forms import ClientForm, ChitfundUserForm, clientAssignForm, clientCategoryUpdateForm
from django.views import generic
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from .mixins import ClientLoginRequiredMixin, ChitfundAccessMixin
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView

# Class based view
# CRUD - Create, Retrieve, Update, Delete, List view


class ClientsignupView(generic.CreateView):
    template_name = 'registration/signup.html'
    form_class = ChitfundUserForm

    def form_valid(self, form):
        try:
            # Print the SQL query
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM client_user LIMIT 1")
                desc = cursor.description
                print("Database columns:", [col[0] for col in desc])

            # Get the selected apps from POST data
            selected_apps = {
                'app_chitfund': 'is_chitfund_user',
                'app_namegen': 'is_namegen_user',
                'app_food': 'is_food_app_user',
                'app_ocr': 'is_ocr_app_user',
                'app_transcribe': 'is_transcribe_app_user',
                'app_chatbot': 'is_chatbot_user',
                'app_kuries': 'is_kuries_user'
            }
            
            # Set the user permissions based on selected apps
            user = form.save(commit=False)
            for app_name, field_name in selected_apps.items():
                if self.request.POST.get(app_name):
                    setattr(user, field_name, True)
            
            user.save()
            return super().form_valid(form)
        except Exception as e:
            print(f"Error in form_valid: {str(e)}")
            raise

    def get_success_url(self) -> str:
        return reverse("login")


# Create your views here.
# request is the parameter for the function

class ClientListView(ClientLoginRequiredMixin, generic.ListView):
    template_name = 'client/client_list.html'
    context_object_name = "clients"

    def get_queryset(self):
        user = self.request.user

        if user.is_chitfund_owner or user.is_chitfund_user:
            queryset = Client.objects.filter(owner=user.userprofile, chitfundName__isnull=False)
        
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = self.request.user
        total_clients = Client.objects.filter(owner=user.userprofile).count()
        context.update({
            "total_clients": total_clients
        })
        return context

def Client_list(request):
    clients = Client.objects.all()


    context = {
        "clients": clients
    }
    return render(request, 'client/client_list.html', context)


class ClientDetailView(ClientLoginRequiredMixin, generic.DetailView):
    template_name = 'client/client_info.html'
    context_object_name = "client"

    def get_queryset(self):
        user = self.request.user
        return Client.objects.filter(owner=user.userprofile)

def Client_info(request,pk):
    #print(pk)
    client = Client.objects.get(id=pk)
    #print(client)
    context = {'client':client}
    return render(request,'client/client_info.html', context)


class ClientCreateView(ClientLoginRequiredMixin, generic.CreateView):
    template_name = 'client/client_create.html'
    form_class = ClientForm

    def get_success_url(self):
        return reverse("client:client-list")

    def form_valid(self, form):
        user = self.request.user
        form.instance.owner = user.userprofile
        send_mail(
            subject="A client has been created",
            message="Go to the site to see the new client",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=["test@test.com"]
        )
        return super(ClientCreateView, self).form_valid(form)



def Client_create(request):
    form = ClientForm()
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            #Client.objects.create(instance=form)
            # new instance of the model saved int he db
            form.save()

            return redirect('client:client-list')


    context={
        'form': form
    }
    return render(request,'client/client_create.html', context)



class ClientUpdateView(ChitfundAccessMixin, generic.UpdateView):
    template_name = 'client/client_update.html'
    form_class = ClientForm
    context_object_name = "client"

    def get_queryset(self):
        user = self.request.user
        return Client.objects.filter(owner=user.userprofile)

    def get_success_url(self):
        return reverse("client:client-list")#,kwargs={"pk":self.get_object.id})


def Client_update(request,pk):
    client = Client.objects.get(id=pk)

    form = ClientForm(instance=client)

    if request.method == 'POST':
        form = ClientForm(request.POST,instance=client)
        if form.is_valid():
            print(form.cleaned_data)
            form.save()
            return redirect('client:client-info', pk=client.id)

    context ={

            'ClientForm':form,
            'client':client
    }

    return render(request,'client/client_update.html',context)


class ClientDeleteView(ChitfundAccessMixin, generic.DeleteView):
    template_name = 'client/client_delete.html'
    context_object_name = "client"

    def get_queryset(self):
        user = self.request.user
        return Client.objects.filter(owner=user.userprofile)

    def get_success_url(self):
        return reverse("client:client-list")


def Client_delete(request, pk):
    client = Client.objects.get(id=pk)
    client.delete()
    return redirect('client:client-list')



class clientAssignView(ChitfundAccessMixin, generic.UpdateView):
    template_name = 'client/client_assign.html'
    form_class = clientAssignForm
    context_object_name = "client"

    def get_form_kwargs(self,**kwargs):
        kwargs = super(clientAssignView, self).get_form_kwargs(**kwargs)

        kwargs.update({
            "request": self.request
        })
        return kwargs

    def get_queryset(self):
        user = self.request.user
        return Client.objects.filter(owner=user.userprofile)

    def get_success_url(self):
        return reverse("client:client-list")

    def form_valid(self, form):
        self.object.chitfundName = form.cleaned_data["chitfund"]
        self.object.save()
        return super(clientAssignView, self).form_valid(form)


class categoryListView(ClientLoginRequiredMixin, generic.ListView):
    template_name = 'client/client_category_view.html'
    context_object_name = "category_list"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super(categoryListView, self).get_context_data(**kwargs)
        user = self.request.user
        queryset = Category.objects.filter(owner=user.userprofile)
        context.update({
            "unassigned_clients": Client.objects.filter(owner=user.userprofile, category__isnull=True)
        })
        return context

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(owner=user.userprofile)

class categoryDetailView(ClientLoginRequiredMixin, generic.DetailView):
    template_name = 'client/client_category_detail.html'
    context_object_name = "category"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super(categoryDetailView, self).get_context_data(**kwargs)
        user = self.request.user
        queryset = Category.objects.filter(owner=user.userprofile)
        context.update({
            "unassigned_clients": Client.objects.filter(owner=user.userprofile, category__isnull=True)
        })
        return context

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(owner=user.userprofile)

class clientCategoryupdateView(ClientLoginRequiredMixin, generic.UpdateView):
    template_name = 'client/client_category_update.html'
    form_class = clientCategoryUpdateForm
    context_object_name = "client"

    def get_queryset(self):
        user = self.request.user
        return Client.objects.filter(owner=user.userprofile)

    def get_success_url(self):
        return reverse("client:client-list")

class ClientSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'client/settings.html'
    
    def post(self, request, *args, **kwargs):
        if 'update_profile' in request.POST:
            # Handle profile update
            username = request.POST.get('username')
            email = request.POST.get('email')
            
            user = request.user
            if username and username != user.username:
                user.username = username
            if email and email != user.email:
                user.email = email
            user.save()
            messages.success(request, 'Profile updated successfully!')
            
        elif 'change_password' in request.POST:
            # Handle password change
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            user = request.user
            if not user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            else:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password changed successfully! Please log in again.')
                return redirect('login')
                
        return self.get(request, *args, **kwargs)

@login_required
def ClientRestrict(request):
    return render(request, 'client/client_restrict.html')
from typing import Any
from django.db.models.query import QuerySet
from django.forms.models import BaseModelForm
from django.core.mail import send_mail
#from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from .models import User, ChitFund, Client, Category
from .forms import ClientForm, ChitfundUserForm, clientAssignForm, clientCategoryUpdateForm
# class functions of django
from django.views import generic
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from kuries.mixins import ChitfundLoginRequiredMixin
from .mixins import ClientLoginRequiredMixin
from django.contrib.auth.decorators import login_required

# Class based view
# CRUD - Create, Retrieve, Update, Delete, List view


class ClientsignupView(generic.CreateView):
    template_name = 'registration/signup.html'
    form_class = ChitfundUserForm

    # when the form is saved successfully
    def get_success_url(self) -> str:
        # same as redirect
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
        # if self.request.user.is_chitfund_user:
        #     queryset = Client.objects.filter(owner=user.chitfund.owner, chitfundName__isnull=False)
        #     queryset = queryset.filter(chitfundName__user= user)

        return queryset

    # how to update the context of the class already ceated
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        user = self.request.user
        # get the context if already created
        context = super(ClientListView, self).get_context_data(**kwargs)
        #print(user.is_chitfund_owner)
        if user.is_chitfund_owner:
            queryset = Client.objects.filter(owner=user.userprofile,
                                             chitfundName__isnull=True)
            #print(queryset.exists)
            context.update({
                "unassigned_clients": queryset
            })
            #print(context)
        return context

def Client_list(request):
    clients = Client.objects.all()


    context = {
        "clients": clients
    }
    return render(request, 'client/client_list.html', context)


class ClientDetailView(ClientLoginRequiredMixin, generic.DetailView):
    template_name = 'client/client_info.html'
    #queryset = Client.objects.all() # default is object_list
    context_object_name = "client"
    def get_queryset(self):
        user = self.request.user

        if user.is_chitfund_owner:
            queryset = Client.objects.filter(owner=user.userprofile)
        if self.request.user.is_chitfund_user:
            queryset = Client.objects.filter(owner=user.chitfund.owner)
            queryset = queryset.filter(chitfundName__user= user)

        return queryset

def Client_info(request,pk):
    #print(pk)
    client = Client.objects.get(id=pk)
    #print(client)
    context = {'client':client}
    return render(request,'client/client_info.html', context)


class ClientCreateView(ClientLoginRequiredMixin, generic.CreateView):
    template_name = 'client/client_create.html'
    form_class = ClientForm

    # when the form is saved successfully
    def get_success_url(self) -> str:
        # same as redirect
        return reverse("client:client-list")

    # Overwriting the method mentioned in CreateView Django to
    # send emails
    def form_valid(self, form):
        
        # To send the email
        send_mail(subject= f"You have added {form.cleaned_data['first_name']} as a new client ",
                  message=f"""
Hello {self.request.user.username},
You have added another client to your name.
Please feel free to Update or add new clients.
Thank you
Regards,
Eneru Solutions
                            """,
                  from_email=settings.EMAIL_HOST_USER,

                  recipient_list=[self.request.user.email]) # instead put request.user.email


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



class ClientUpdateView(ChitfundLoginRequiredMixin, generic.UpdateView):
    template_name = 'client/client_update.html'
    form_class = ClientForm

    # in Update VIew we have a get_object() parameter
    # which can be used for ger_success_url as well
    #queryset = Client.objects.all()
    context_object_name = "client"
    def get_queryset(self):
        user = self.request.user

        queryset = Client.objects.filter(owner=user.userprofile)

        return queryset
    # when the form is saved successfully
    def get_success_url(self) -> str:
        # same as redirect
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


class ClientDeleteView(ChitfundLoginRequiredMixin, generic.DeleteView):
    template_name = 'client/client_delete.html'
    #queryset = Client.objects.all()
    context_object_name = "client"
    # when the form is saved successfully
    def get_queryset(self):
        user = self.request.user

        queryset = Client.objects.filter(owner=user.userprofile)

        return queryset

    def get_success_url(self) -> str:
        # same as redirect
        return reverse("client:client-list")


def Client_delete(request, pk):
    client = Client.objects.get(id=pk)
    client.delete()
    return redirect('client:client-list')



class clientAssignView(ChitfundLoginRequiredMixin, generic.FormView):
    template_name = 'client/client_assign.html'
    context_object_name = "client"
    form_class = clientAssignForm

    # To pass the request user to the forms.py file
    def get_form_kwargs(self,**kwargs):
        kwargs = super(clientAssignView, self).get_form_kwargs(**kwargs)

        kwargs.update({
            "request": self.request
        })
        return kwargs

    # def get_queryset(self):
    #     user = self.request.user
    #     queryset = Client.objects.filter(owner=user.userprofile)
    #     return queryset

    def get_success_url(self) -> str:
        # same as redirect
        return reverse("client:client-list")

    def form_valid(self, form):
        #print("Data is :",form.data)
        sel_chitfund = form.cleaned_data["chitfund"]
        client = Client.objects.get(id=self.kwargs["pk"])
        # user = self.request.user
        # client = Client.objects.filter(owner=user.userprofile)
        client.chitfundName = sel_chitfund
        client.save()
        return super(clientAssignView, self).form_valid(form)


class categoryListView(ClientLoginRequiredMixin, generic.ListView):
    template_name = 'client/client_category_view.html'
    context_object_name = "category_list"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        user = self.request.user
        context = super(categoryListView, self).get_context_data(**kwargs)
        if user.is_chitfund_owner:
            queryset = Client.objects.filter(owner=user.userprofile)
        else:
            queryset = Client.objects.filter(owner=user.chitfund.owner)
        context.update({
            "unassigned_client_count": queryset.filter(category__isnull=True).count()
        })
        return context

    def get_queryset(self):
        user = self.request.user

        if user.is_chitfund_owner:
            queryset = Category.objects.filter(owner=user.userprofile)
        else:
            queryset = Category.objects.filter(owner=user.chitfund.owner)

        #print(queryset)

        return queryset


class categoryDetailView(ClientLoginRequiredMixin, generic.DetailView):
    template_name = 'client/client_category_detail.html'
    context_object_name = "category"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        user = self.request.user
        context = super(categoryDetailView, self).get_context_data(**kwargs)

        # Both of the below lines do the same thing basically
        #clients = Client.objects.filter(category=self.get_object())
        #self.get_object().client_set.all()

        # because we added related names in the model Client
        # we can do like this below
        clients = self.get_object().clients.all()

        # filter the clients associated with the user
        clients = clients.filter(owner=user.userprofile)


        context.update({
            "clients": clients
        })
        return context


    def get_queryset(self):
        user = self.request.user

        if user.is_chitfund_owner:
            queryset = Category.objects.filter(owner=user.userprofile)
        if user.is_chitfund_user:
            queryset = Category.objects.filter(owner=user.chitfund.owner)

        return queryset


class clientCategoryupdateView(ClientLoginRequiredMixin, generic.UpdateView):
    template_name = 'client/client_category_update.html'
    form_class = clientCategoryUpdateForm
    context_object_name = "client"
    def get_queryset(self):
        user = self.request.user

        if user.is_chitfund_owner:
            queryset = Client.objects.filter(owner=user.userprofile)
        if user.is_chitfund_user:
            queryset = Client.objects.filter(owner=user.chitfund.owner)

            # filter for the user who is logged in
            queryset = queryset.filter(chitfundName__user=user)

        return queryset

    def get_success_url(self) -> str:
        return reverse('client:client-info',kwargs={"pk":self.get_object().id})

#@login_required('login')
def ClientRestrict(request):
    return render(request,'client/client_restrict.html')
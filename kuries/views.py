from django.shortcuts import reverse
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from client.models import ChitFund
from .forms import chitfundModelForm
from .mixins import ChitfundLoginRequiredMixin
from django.conf import settings
from django.core.mail import send_mail
# Create your views here.



class chitfundlistview(ChitfundLoginRequiredMixin, generic.ListView):
    template_name = "kuries/chitfund_list.html"


    # second way of getting the query set
    def get_queryset(self):
        print(self.request.user.userprofile)
        request_user_owner = self.request.user.userprofile
        return ChitFund.objects.filter(owner=request_user_owner)


class chitfundCreateview(ChitfundLoginRequiredMixin, generic.CreateView):
    template_name = "kuries/chitfund_create.html"
    form_class = chitfundModelForm

    def get_success_url(self):
        return reverse("kuries:chitfund-list")

    def form_valid(self, form):
        chitfund = form.save(commit=False)
        chitfund.owner = self.request.user.userprofile
        #chitfund.set_password(random)
        chitfund.save()
        send_mail(
            subject= f"{chitfund.name} successfully created !",
            message = f"You have successfully create your own chitfund {chitfund.name} under the owner name {chitfund.owner}",
            from_email=settings.EMAIL_HOST_USER,

            recipient_list=[self.request.user.email]
        )
        return super(chitfundCreateview, self).form_valid(form)

class chitfundDetaiView(ChitfundLoginRequiredMixin, generic.DetailView):
    template_name = "kuries/chitfund_info.html"
    # sexond way of getting the query set
    def get_queryset(self):
        return ChitFund.objects.all()


class chitfundUpdateView(ChitfundLoginRequiredMixin, generic.UpdateView):
    template_name = 'kuries/chitfund_update.html'
    form_class = chitfundModelForm

    def get_queryset(self):
        return ChitFund.objects.all()

    context_object_name = "chitfund"
    # when the form is saved successfully
    def get_success_url(self) -> str:
        # same as redirect
        return reverse("kuries:chitfund-list")

class chitfundDeleteView(ChitfundLoginRequiredMixin, generic.DeleteView):
    template_name = 'kuries/chitfund_delete.html'

    def get_queryset(self):
        request_user_owner = self.request.user.userprofile
        return ChitFund.objects.filter(owner=request_user_owner)

    context_object_name = "chitfund"
    # when the form is saved successfully
    def get_success_url(self) -> str:
        # same as redirect
        return reverse("kuries:chitfund-list")
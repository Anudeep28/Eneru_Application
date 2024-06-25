from django import forms
from django.forms import ModelForm
from .models import Client, User, ChitFund
from django.contrib.auth.forms import UserCreationForm


# class ClientForm(forms.Form):
#     first_name = forms.CharField()
#     last_name = forms.CharField()
#     age = forms.IntegerField(min_value=18)


class ClientForm(ModelForm):
    class Meta:
        model = Client

        fields = '__all__'

class ChitfundUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username','email','password1','password2','is_chitfund_owner','is_chitfund_user','is_namegen_user')
        # we can also do it in this way
        # fields = ("username",)
        # field_classes = {"username" : UsernamField}

class clientAssignForm(forms.Form):
    # Django provides us with Model choice instaead which takes in the
    # queryset from the models
    chitfund = forms.ModelChoiceField(queryset=ChitFund.objects.none())

    # Creating a dynamic updating queryset for the form above
    def __init__(self, *args, **kwargs):
        # getting the request from views here
        request = kwargs.pop("request")
        chitfunds = ChitFund.objects.filter(owner=request.user.userprofile)
        super(clientAssignForm, self).__init__(*args, **kwargs)
        self.fields["chitfund"].queryset = chitfunds

class clientCategoryUpdateForm(ModelForm):

    class Meta:
        model = Client
        fields = ['category']


class LoginUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username','password']
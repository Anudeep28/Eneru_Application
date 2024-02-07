from django import forms
from client.models import ChitFund



class chitfundModelForm(forms.ModelForm):
    class Meta:
        model = ChitFund
        fields = ('name','about','address','state','country','pin')#,'user')        

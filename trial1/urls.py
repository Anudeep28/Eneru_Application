# This file is mainly to organise the routes between views
# this file has been included in project urls.py file
from django.urls import path
from .views import (
    NameGeneratorListView, 
    NameGeneratorCreateView,
    NameGeneratorView  
)

app_name = "trial1"

urlpatterns = [
    path('', NameGeneratorListView.as_view(), name='namegen-list'),
    path('create/', NameGeneratorCreateView.as_view(), name='namegen-create'),
    path('generate/', NameGeneratorView.as_view(), name='name-generator'),  
]
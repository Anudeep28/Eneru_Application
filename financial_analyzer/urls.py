from django.urls import path
from . import views

app_name = 'financial_analyzer'

urlpatterns = [
    path('', views.WelcomeView.as_view(), name='welcome'),
]

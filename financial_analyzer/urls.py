from django.urls import path
from . import views

app_name = 'financial_analyzer'

urlpatterns = [
    path('stock-input/', views.ConversationView.as_view(), name='stock-input'),
]

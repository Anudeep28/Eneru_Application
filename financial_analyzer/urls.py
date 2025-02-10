from django.urls import path
from . import views

app_name = 'financial_analyzer'

urlpatterns = [
    path('', views.StockInputView.as_view(), name='stock-input'),
]

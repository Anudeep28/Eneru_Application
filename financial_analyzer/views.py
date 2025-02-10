from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from .mixins import FinancialAnalyzerSubscriptionRequiredMixin

# Create your views here.

@method_decorator(login_required, name='dispatch')
class StockInputView(FinancialAnalyzerSubscriptionRequiredMixin, TemplateView):
    template_name = 'financial_analyzer/stock_input.html'

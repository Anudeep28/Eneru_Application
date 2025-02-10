from client.mixins import SubscriptionRequiredMixin

class FinancialAnalyzerSubscriptionRequiredMixin(SubscriptionRequiredMixin):
    app_permission = 'is_financial_analyzer_user'
    app_name = 'Financial Analyzer'

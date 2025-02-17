from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class AppAccessMixin(AccessMixin):
    """Base mixin to verify that the current user has access to the specific app."""
    app_permission = None  # Should be set in child classes (e.g., 'is_chitfund_user')
    app_name = None       # Should be set in child classes (e.g., 'Chitfund')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        if not self.app_permission or not hasattr(request.user, self.app_permission):
            raise ValueError(f"app_permission not properly set for {self.__class__.__name__}")
        
        # Clear any existing unauthorized access messages for this specific app
        storage = messages.get_messages(request)
        for message in storage:
            if f"not authorized to use the {self.app_name}" in str(message):
                storage.used = True
            
        if not getattr(request.user, self.app_permission):
            messages.error(request, f"You are not authorized to use the {self.app_name} app. Please subscribe to access this feature.", extra_tags=f'unauthorized_{self.app_name.lower().replace(" ", "_")}')
            return redirect('landing-page')
            
        return super().dispatch(request, *args, **kwargs)

class ChitfundAccessMixin(AppAccessMixin):
    app_permission = 'is_chitfund_user'
    app_name = 'Chitfund'

class NamegenAccessMixin(AppAccessMixin):
    app_permission = 'is_namegen_user'
    app_name = 'Name Generator'

class FoodAppAccessMixin(AppAccessMixin):
    app_permission = 'is_food_app_user'
    app_name = 'Food Ordering'

class OCRAppAccessMixin(AppAccessMixin):
    app_permission = 'is_ocr_app_user'
    app_name = 'OCR'

class TranscribeAppAccessMixin(AppAccessMixin):
    app_permission = 'is_transcribe_app_user'
    app_name = 'Transcription'

class ChatbotAccessMixin(AppAccessMixin):
    app_permission = 'is_chatbot_user'
    app_name = 'Chatbot'

class KuriesAccessMixin(AppAccessMixin):
    app_permission = 'is_kuries_user'
    app_name = 'Kuries'

class FinancialAnalyzerAccessMixin(AppAccessMixin):
    app_permission = 'is_financial_analyzer_user'
    app_name = 'Financial Analyzer'

class ClientLoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and the owner."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not any([request.user.is_chitfund_owner,request.user.is_chitfund_user]):
            return redirect("client:client-restrict")
        return super().dispatch(request, *args, **kwargs)

class SubscriptionRequiredMixin:
    app_permission = None  # Should be set in child classes (e.g., 'is_financial_analyzer_user')
    app_name = None       # Should be set in child classes (e.g., 'Financial Analyzer')

    def dispatch(self, request, *args, **kwargs):
        # Check if app_permission is properly set
        if not self.app_permission or not hasattr(request.user, self.app_permission):
            raise ValueError(f"app_permission not properly set for {self.__class__.__name__}")
        
        # Check if user is subscribed to the app
        if not getattr(request.user, self.app_permission):
            messages.error(request, f"You are not authorized to use the {self.app_name} app. Please subscribe to access this feature.", 
                         extra_tags=f'unauthorized_{self.app_name.lower().replace(" ", "_")}')
            return redirect('landing-page')
        
        return super().dispatch(request, *args, **kwargs)

class ChitFundSubscriptionRequiredMixin(SubscriptionRequiredMixin):
    app_permission = 'is_chitfund_user'
    app_name = 'Chitfund'

class NameGenSubscriptionRequiredMixin(SubscriptionRequiredMixin):
    app_permission = 'is_namegen_user'
    app_name = 'Name Generator'

class FoodAppSubscriptionRequiredMixin(SubscriptionRequiredMixin):
    app_permission = 'is_food_app_user'
    app_name = 'Food App'

class OCRAppSubscriptionRequiredMixin(SubscriptionRequiredMixin):
    app_permission = 'is_ocr_app_user'
    app_name = 'OCR App'

class TranscribeAppSubscriptionRequiredMixin(SubscriptionRequiredMixin):
    app_permission = 'is_transcribe_app_user'
    app_name = 'Transcribe App'

class ChatbotSubscriptionRequiredMixin(SubscriptionRequiredMixin):
    app_permission = 'is_chatbot_user'
    app_name = 'Chatbot'

class KuriesSubscriptionRequiredMixin(SubscriptionRequiredMixin):
    app_permission = 'is_kuries_user'
    app_name = 'Kuries'

class FinancialAnalyzerSubscriptionRequiredMixin(SubscriptionRequiredMixin):
    app_permission = 'is_financial_analyzer_user'
    app_name = 'Financial Analyzer'

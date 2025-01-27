from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages

class AppAccessMixin(AccessMixin):
    """Base mixin to verify that the current user has access to the specific app."""
    app_permission = None  # Should be set in child classes (e.g., 'is_chitfund_user')
    app_name = None       # Should be set in child classes (e.g., 'Chitfund')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        if not self.app_permission or not hasattr(request.user, self.app_permission):
            raise ValueError(f"app_permission not properly set for {self.__class__.__name__}")
            
        if not getattr(request.user, self.app_permission):
            messages.error(request, f"You are not authorized to use the {self.app_name} app. Please subscribe to access this feature.")
            return redirect('login')
            
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

class ClientLoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and the owner."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not any([request.user.is_chitfund_owner,request.user.is_chitfund_user]):
            return redirect("client:client-restrict")
        return super().dispatch(request, *args, **kwargs)

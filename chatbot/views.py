from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.views import generic
from client.mixins import ChatbotAccessMixin
import google.generativeai as genai

# Replace with your actual API key
API_KEY = settings.GEMINI_API_KEY       
genai.configure(api_key=API_KEY)

def generate_response(user_input):
    try:
        # Initialize chat model
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        
        # Generate response
        response = model.generate_content(user_input)
        return response.text
    except Exception as e:
        return str(e)

class ChatbotIndexView(ChatbotAccessMixin, generic.TemplateView):
    template_name = 'chatbot/geminiChat_test.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['csrf_token'] = get_token(self.request)
        return context

class ChatbotChatView(ChatbotAccessMixin, generic.View):
    def post(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            user_input = request.POST.get('message')
            response = generate_response(user_input)
            return JsonResponse({'response': response, 'status': 'success'})
        return JsonResponse({'status': 'error', 'error': 'Invalid request method'})
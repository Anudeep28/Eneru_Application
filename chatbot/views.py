from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from client.mixins import ChatbotAccessMixin
import google.generativeai as genai
from django.conf import settings
from .models import Conversation, Message
import json

# Configure the Gemini model
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

class ChatbotIndexView(LoginRequiredMixin, ChatbotAccessMixin, View):
    template_name = 'chatbot/geminiChat.html'

    def get(self, request):
        # Ensure session is created first
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
        
        # Get or create a conversation for this session
        conversation, created = Conversation.objects.get_or_create(
            session_id=session_id,
            user=request.user if request.user.is_authenticated else None
        )
        
        # Get recent messages
        recent_messages = Message.objects.filter(conversation=conversation).order_by('timestamp')[:10]
        
        context = {
            'conversation_id': conversation.id,
            'recent_messages': recent_messages
        }
        return render(request, self.template_name, context)

class ChatbotChatView(LoginRequiredMixin, ChatbotAccessMixin, View):
    def post(self, request):
        try:
            message = request.POST.get('message', '').strip()
            if not message:
                return JsonResponse({'status': 'error', 'message': 'Message is required'})

            # Ensure session is created first
            if not request.session.session_key:
                request.session.create()
            session_id = request.session.session_key
            
            # Get or create conversation
            conversation, created = Conversation.objects.get_or_create(
                session_id=session_id,
                user=request.user if request.user.is_authenticated else None
            )

            # Save user message
            user_message = Message.objects.create(
                conversation=conversation,
                content=message,
                is_user=True
            )

            # Get conversation history
            history = Message.objects.filter(conversation=conversation).order_by('timestamp')
            
            # Build conversation context
            chat_history = []
            for msg in history:
                role = "user" if msg.is_user else "assistant"
                chat_history.append({"role": role, "parts": [msg.content]})

            # Start chat and get response
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(message)
            
            if response.text:
                # Save bot response
                bot_message = Message.objects.create(
                    conversation=conversation,
                    content=response.text,
                    is_user=False
                )
                
                return JsonResponse({
                    'status': 'success',
                    'response': response.text,
                    'conversation_id': conversation.id
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to get response from the bot'
                })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
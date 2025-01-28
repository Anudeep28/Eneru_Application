from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from django.views import generic
from client.mixins import ChatbotAccessMixin
import google.generativeai as genai
import re

# Replace with your actual API key
API_KEY = settings.GEMINI_API_KEY       
genai.configure(api_key=API_KEY)

def format_code_blocks(text):
    # Split text into blocks (code and non-code)
    parts = re.split(r'(```[\s\S]*?```)', text)
    
    formatted_parts = []
    for part in parts:
        if part.startswith('```') and part.endswith('```'):
            # Handle code blocks
            # Extract language if specified
            lang_match = re.match(r'```(\w+)?\n', part)
            lang = lang_match.group(1) if lang_match else ''
            
            # Clean up the code block
            code = part.replace('```' + (lang if lang else ''), '', 1)  # Remove opening fence
            code = code.rstrip('```')  # Remove closing fence
            code = code.strip()  # Remove extra whitespace
            
            # Reconstruct code block with proper formatting
            formatted_parts.append(f'```{lang}\n{code}\n```')
        else:
            formatted_parts.append(part)
    
    return ''.join(formatted_parts)

def format_markdown(text):
    # First, handle code blocks specially
    text = format_code_blocks(text)
    
    # Handle inline code
    text = re.sub(r'`([^`]+)`', r'`\1`', text)
    
    # Format lists
    text = re.sub(r'(?m)^(\d+)\.\s+', r'\1. ', text)  # Numbered lists
    text = re.sub(r'(?m)^[-*]\s+', '- ', text)        # Bullet points
    
    # Format headers
    text = re.sub(r'(?m)^(#{1,6})\s*', r'\1 ', text)
    
    # Format blockquotes
    text = re.sub(r'(?m)^>\s*', '> ', text)
    
    # Ensure proper spacing around headers and lists
    text = re.sub(r'\n{3,}', '\n\n', text)  # Remove extra blank lines
    text = re.sub(r'(?m)^(#{1,6}|\d+\.|-|\*)', r'\n\1', text)  # Add newline before headers and lists
    
    return text.strip()

def generate_response(user_input):
    try:
        # Initialize chat model with specific configuration
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config={
                'temperature': 0.7,
                'top_p': 0.8,
                'top_k': 40,
            }
        )
        
        # Generate response with specific prompt engineering
        prompt = f"""Please provide a clear and well-formatted response using markdown.
For code examples:
- Use proper code blocks with language specification
- Ensure proper indentation
- Add comments where necessary

For explanations:
- Use appropriate headers
- Use bullet points or numbered lists where applicable
- Highlight important terms using bold or inline code

Question: {user_input}
"""
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Format the response text for proper markdown rendering
        formatted_response = format_markdown(response.text)
        
        return formatted_response
    except Exception as e:
        return str(e)

class ChatbotIndexView(ChatbotAccessMixin, generic.TemplateView):
    template_name = 'chatbot/geminiChat.html'
    
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
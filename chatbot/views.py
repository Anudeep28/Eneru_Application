from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import google.generativeai as genai
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token

# Replace with your actual API key
API_KEY = settings.GEMINI_API_KEY       
genai.configure(api_key=API_KEY)

@login_required(login_url='login')
def index(request):
    # print("start here")
    csrf_token = get_token(request)
    return render(request, 'chatbot/geminiChat_test.html', {'csrf_token': csrf_token})

@login_required(login_url='login')
def chat(request):
    # print("received post 1")
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method=='POST':
        user_input = request.POST.get('message')
        # Process the user input and generate the response
        response = generate_response(user_input)
        # print("Received Post 2")
        return JsonResponse({'response': response, 'status':'success'})
        
    else:
        return JsonResponse({'status':'error','error': 'Invalid request method'})

def generate_response(user_input):
    # Implement your logic to generate the response based on the user input
    chat = genai.GenerativeModel(model_name='gemini-1.5-flash')
    result = chat.generate_content(user_input)
    
    response = result.text
    return response



# def chat(request):
#     if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method=='POST':
#         user_input = request.POST.get('message')
#         print(request.POST)

#         chat = genai.GenerativeModel(model_name='gemini-1.5-flash')
#         result = chat.generate_content(user_input)
        
#         response = result.text
        
#         return JsonResponse({'response': response})
#     else:
#         return JsonResponse({'error': 'Invalid request method'})
    


#from django.http import JsonResponse
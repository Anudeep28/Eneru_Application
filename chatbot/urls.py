# This file is mainly to organise the routes between views
# this file has been included in project urls.py file
from django.urls import path
from . import views

app_name='chatbot'
# the names are used on href in the html very important for routing
urlpatterns = [
    path('', views.ChatbotIndexView.as_view(), name="chatbotIndex"),
    path('geminiChat/', views.ChatbotChatView.as_view(), name='geminiChat'),
]
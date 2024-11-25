from django.urls import path
from . import views

app_name = 'transcribe_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('transcribe/', views.transcribe_audio, name='transcribe'),
    path('download/markdown/', views.download_markdown, name='download-markdown'),
    path('download/word/', views.download_word, name='download-word'),
]

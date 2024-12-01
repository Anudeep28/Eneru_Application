from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ocr/', include('ocr_app.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('kuries/', include('kuries.urls')),
    path('trial1/', include('trial1.urls')),
    path('transcribe/', include('transcribe_app.urls')),
    path('food/', include('food_app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

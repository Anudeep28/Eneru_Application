"""
URL configuration for chitfund project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .view import LandingPageView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import (LoginView,
                                       LogoutView,
                                       PasswordResetView,
                                       PasswordResetDoneView,
                                       PasswordResetConfirmView,
                                       PasswordResetCompleteView)
from client.views import ClientsignupView
# Namespace to identify the app we are using if we have multiple apps
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', LandingPageView.as_view(), name='landing-page'),
    # Apps usrls
    path('client/', include('client.urls', namespace="client" )),
    path('kuries/', include('kuries.urls', namespace="kuries" )),
    path('namgen/', include('trial1.urls',namespace='namegen')),
    path('chatbot/', include('chatbot.urls',namespace='chatbot')),
    path('ocr/', include('ocr_app.urls', namespace='ocr_app')),
    path('transcribe/', include('transcribe_app.urls', namespace='transcribe_app')),
    path('food/', include('food_app.urls', namespace='food_app')),
    path('enlaw/', include('enlaw.urls')),
    # login
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', ClientsignupView.as_view(), name='signup'),
    path('passwordReset/', PasswordResetView.as_view(), name='password-reset'),
    path('passwordResetDone/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('passwordResetConfirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('passwordResetComplete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

# checkign for debug mode
if settings.DEBUG:
    # this is for user uploads for media files
    #urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

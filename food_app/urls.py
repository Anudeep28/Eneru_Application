from django.urls import path
from . import views

app_name = 'food_app'

urlpatterns = [
    path('', views.index, name='food-index'),
    path('analyze/', views.analyze_image, name='food-analyze'),
]

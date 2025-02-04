from django.urls import path
from . import views

# To identify this App  when we have multiple app
app_name = "client"

urlpatterns = [
    path('', views.ClientListView.as_view(), name='client-list'),

    path('create/', views.ClientCreateView.as_view(), name='client-create'),

    path('<int:pk>/', views.ClientDetailView.as_view(), name='client-info'),

    path('<int:pk>/update/', views.ClientUpdateView.as_view(), name='client-update'),

    path('<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client-delete'),

    path('assign/<int:pk>/', views.clientAssignView.as_view(), name='client-assign'),

    path('category/', views.categoryListView.as_view(), name='client-category'),

    path('categoryDetail/<int:pk>/', views.categoryDetailView.as_view(), name='client-category-detail'),

    path('categoryDetailUpdate/<int:pk>/', views.clientCategoryupdateView.as_view(), name='client-category-update'),

    path('restrict/', views.ClientRestrict, name='client-restrict'),

    path('settings/', views.ClientSettingsView.as_view(), name='client-settings'),
]
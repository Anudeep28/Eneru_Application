
from django.urls import path
from .views import chitfundlistview, chitfundCreateview, chitfundDetaiView, chitfundUpdateView, chitfundDeleteView


# To identify this App  when we have multiple app
app_name = "kuries"

urlpatterns = [
    path('', chitfundlistview.as_view(), name='chitfund-list'),
    path('create/', chitfundCreateview.as_view(), name='chitfund-create'),
    path('<int:pk>', chitfundDetaiView.as_view(), name='chitfund-info'),

    path('update/<int:pk>', chitfundUpdateView.as_view(), name='chitfund-update'),

    path('delete/<int:pk>', chitfundDeleteView.as_view(), name='chitfund-delete')
]
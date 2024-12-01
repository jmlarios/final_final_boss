from django.urls import path
from . import views

app_name = 'menu_app'

urlpatterns = [
    path('menu/<int:restaurant_id>/', views.menu_detail, name='menu_detail'),
    path('upload/', views.upload_menu, name='upload_menu'),  # Add the upload route
]

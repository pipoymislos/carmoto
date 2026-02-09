from django.contrib import admin
from django.urls import path
from cars import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('cars/', views.car_list, name='car_list'),
    path('cars/new/', views.car_create, name='car_create'),
    path('cars/edit/<int:pk>/', views.car_update, name='car_update'),
    path('cars/delete/<int:pk>/', views.car_delete, name='car_delete'),
]

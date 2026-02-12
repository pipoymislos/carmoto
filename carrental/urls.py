from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from cars import views

urlpatterns = [
    # Default Django admin
    path('django-admin/', admin.site.urls),
    
    # Authentication
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-logout/', views.logout_view, name='admin_logout'),
    
    # User Pages
    path('cars/', views.car_list, name='car_list'),
    path('cars/detail/<int:car_id>/', views.car_detail, name='car_detail'),
    path('cars/new/', views.car_create, name='car_create'),
    path('cars/edit/<int:pk>/', views.car_update, name='car_update'),
    path('cars/delete/<int:pk>/', views.car_delete, name='car_delete_user'),
    path('cars/book/<int:car_id>/', views.book_car, name='book_car'),
    
    # User Reservations
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('reservation/<int:pk>/', views.reservation_detail, name='reservation_detail'),
    path('reservation/<int:pk>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    path('reservation/<int:pk>/receipt/', views.download_receipt, name='download_receipt'),
    
    # Admin Pages - Original
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/car/delete/<int:pk>/', views.car_delete_admin, name='car_delete_admin'),
    path('admin/reservation/<int:reservation_id>/<str:status>/', 
         views.reservation_update_status, name='reservation_update_status'),
    
    # NEW Admin Car Management - CONSISTENT NAMING
    path('admin/cars/add/', views.add_car, name='add_car'),
    path('admin/cars/edit/<int:car_id>/', views.edit_car, name='edit_car'),
    path('admin/cars/delete/<int:car_id>/', views.delete_car_admin, name='delete_car_admin'),  # Keep this name
    path('admin/car-list/', views.admin_car_list, name='admin_car_list'),
    path('admin/toggle-car-status/<int:car_id>/', views.toggle_car_status, name='toggle_car_status'),
    
    # NEW Admin Reservation Management
    path('admin/all-reservations/', views.all_reservations, name='all_reservations'),
    path('admin/reservations/<int:reservation_id>/', views.view_reservation, name='view_reservation'),
    path('admin/reservations/<int:reservation_id>/approve/', views.approve_reservation, name='approve_reservation'),
    path('admin/reservations/<int:reservation_id>/reject/', views.reject_reservation, name='reject_reservation'),
    path('admin/reservations/<int:reservation_id>/update/<str:status>/', 
         views.reservation_update_status, name='admin_reservation_update'),
    path('admin/reservations/<int:pk>/receipt/', views.admin_download_receipt, name='admin_download_receipt'),
    
    # AJAX endpoints
    path('check-availability/', views.check_availability, name='check_availability'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
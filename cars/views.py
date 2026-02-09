from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from datetime import date, datetime
from .models import Car, Reservation, User
from .forms import CarForm, RegisterForm, ReservationForm
import json
from django.core import serializers
from django.http import JsonResponse, HttpResponse

# --- Authentication ---
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful! Please login.")
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'cars/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_staff:
                messages.success(request, f"Welcome back, Admin {user.username}!")
                return redirect('admin_dashboard')
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('car_list')
        messages.error(request, "Invalid username or password.")
    return render(request, 'cars/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

# --- Admin Dashboard ---
@staff_member_required
def admin_dashboard(request):
    print("=== DEBUG: Admin Dashboard View Called ===")
    print(f"User: {request.user}, Is Staff: {request.user.is_staff}")
    
    # Get statistics
    total_cars = Car.objects.count()
    available_cars = Car.objects.filter(is_available=True).count()
    total_reservations = Reservation.objects.count()
    pending_reservations = Reservation.objects.filter(status='pending').count()
    approved_reservations = Reservation.objects.filter(status='approved').count()
    total_users = User.objects.filter(is_staff=False).count()
    
    print(f"Stats - Cars: {total_cars}, Available: {available_cars}")
    print(f"Stats - Reservations: {total_reservations}, Pending: {pending_reservations}")
    
    # Get latest data
    cars = Car.objects.all().order_by('-created_at')[:10]
    reservations = Reservation.objects.all().order_by('-created_at')[:10]
    
    # Convert to JSON
    cars_data = serializers.serialize('json', cars)
    reservations_data = serializers.serialize('json', reservations)
    
    print(f"Cars in context: {len(cars)}")
    print(f"Reservations in context: {len(reservations)}")
    
    context = {
        'cars': cars,
        'reservations': reservations,
        'cars_json': cars_data,
        'reservations_json': reservations_data,
        'total_cars': total_cars,
        'available_cars': available_cars,
        'total_reservations': total_reservations,
        'pending_reservations': pending_reservations,
        'approved_reservations': approved_reservations,
        'total_users': total_users,
        'current_date': datetime.now().strftime("%B %d, %Y"),
    }
    
    print("=== DEBUG: Rendering Template ===")
    return render(request, 'cars/admin_dashboard.html', context)

# --- NEW: Add Car for Admin ---
@staff_member_required
def add_car(request):
    if request.method == 'POST':
        brand = request.POST.get('brand')
        name = request.POST.get('name')
        description = request.POST.get('description')
        price_per_day = request.POST.get('price_per_day')
        transmission = request.POST.get('transmission')
        fuel_type = request.POST.get('fuel_type')
        seats = request.POST.get('seats', 4)
        is_available = request.POST.get('is_available') == 'on'
        
        car = Car.objects.create(
            brand=brand,
            name=name,
            description=description,
            price_per_day=price_per_day,
            transmission=transmission,
            fuel_type=fuel_type,
            seats=seats,
            is_available=is_available,
            created_by=request.user
        )
        
        if 'image' in request.FILES:
            car.image = request.FILES['image']
            car.save()
        
        messages.success(request, f'Car {brand} {name} added successfully!')
        return redirect('admin_dashboard')
    
    return render(request, 'cars/add_car.html')

# --- NEW: Edit Car for Admin ---
@staff_member_required
def edit_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    
    if request.method == 'POST':
        car.brand = request.POST.get('brand')
        car.name = request.POST.get('name')
        car.description = request.POST.get('description')
        car.price_per_day = request.POST.get('price_per_day')
        car.transmission = request.POST.get('transmission')
        car.fuel_type = request.POST.get('fuel_type')
        car.seats = request.POST.get('seats', 4)
        car.is_available = request.POST.get('is_available') == 'on'
        
        if 'image' in request.FILES:
            car.image = request.FILES['image']
        
        car.save()
        messages.success(request, f'Car {car.brand} {car.name} updated successfully!')
        return redirect('admin_dashboard')
    
    context = {'car': car}
    return render(request, 'cars/edit_car.html', context)

# --- NEW: Delete Car for Admin ---
@staff_member_required
def delete_car_admin(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    if request.method == 'POST':
        car_name = str(car)
        car.delete()
        messages.success(request, f"Car '{car_name}' deleted successfully.")
        return redirect('admin_dashboard')
    
    # If GET request, show confirmation page
    return render(request, 'cars/car_confirm_delete.html', {'car': car})

# --- NEW: View Reservation Details ---
@staff_member_required
def view_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    context = {'reservation': reservation}
    return render(request, 'cars/view_reservation.html', context)

# --- NEW: Approve Reservation ---
@staff_member_required
def approve_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    reservation.status = 'approved'
    reservation.save()
    messages.success(request, f'Reservation #{reservation_id} approved successfully!')
    return redirect('admin_dashboard')

# --- NEW: Reject Reservation ---
@staff_member_required
def reject_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    reservation.status = 'rejected'
    reservation.save()
    messages.success(request, f'Reservation #{reservation_id} rejected!')
    return redirect('admin_dashboard')

# --- NEW: Toggle Car Status ---
@staff_member_required
def toggle_car_status(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    car.is_available = not car.is_available
    car.save()
    
    status = 'available' if car.is_available else 'unavailable'
    messages.success(request, f'Car status changed to {status}')
    return redirect('admin_dashboard')

# --- NEW: All Reservations View ---
@staff_member_required
def all_reservations(request):
    status_filter = request.GET.get('status', '')
    if status_filter:
        reservations = Reservation.objects.filter(status=status_filter).order_by('-created_at')
    else:
        reservations = Reservation.objects.all().order_by('-created_at')
    
    context = {'reservations': reservations, 'status_filter': status_filter}
    return render(request, 'cars/all_reservations.html', context)

# --- NEW: All Cars View for Admin ---
@staff_member_required
def admin_car_list(request):
    cars = Car.objects.all().order_by('-created_at')
    context = {'cars': cars}
    return render(request, 'cars/admin_car_list.html', context)

# --- Existing Functions (keep these) ---
@staff_member_required
def reservation_update_status(request, reservation_id, status):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    if status in ['approved', 'rejected', 'completed', 'cancelled']:
        reservation.status = status
        reservation.save()
        messages.success(request, 
            f"Reservation #{reservation_id} status updated to {status}. "
            f"Notification sent to {reservation.contact_email}")
    return redirect('admin_dashboard')

@staff_member_required
def car_delete_admin(request, pk):
    car = get_object_or_404(Car, pk=pk)
    if request.method == 'POST':
        car_name = str(car)
        car.delete()
        messages.success(request, f"Car '{car_name}' deleted successfully.")
    return redirect('admin_dashboard')

# --- User Booking ---
@login_required
def book_car(request, car_id):
    car = get_object_or_404(Car, id=car_id, is_available=True)
    
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.car = car
            reservation.customer = request.user
            reservation.total_amount = car.total_price(
                reservation.start_date, 
                reservation.end_date
            )
            reservation.save()
            
            messages.success(request, 
                f"Car {car.brand} {car.name} booked successfully! "
                f"Your reservation ID is #{reservation.id}. "
                f"We have sent a confirmation to {reservation.contact_email}. "
                f"Total amount: ₱{reservation.total_amount}")
            return redirect('car_list')
    else:
        form = ReservationForm(initial={
            'contact_email': request.user.email if request.user.email else '',
        })
    
    return render(request, 'cars/book_car.html', {
        'car': car,
        'form': form,
        'today': date.today().isoformat()
    })

# --- User Car List ---
@login_required
def car_list(request):
    cars = Car.objects.filter(is_available=True)
    
    # Get user's reservations
    user_reservations = Reservation.objects.filter(customer=request.user).order_by('-created_at')
    
    return render(request, 'cars/car_list.html', {
        'cars': cars,
        'user_reservations': user_reservations
    })

# --- User CRUD for cars ---
@login_required
def car_create(request):
    if not request.user.is_staff:
        messages.error(request, "Only admin can add cars.")
        return redirect('car_list')
    
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save(commit=False)
            car.created_by = request.user
            car.save()
            messages.success(request, f"Car {car.brand} {car.name} added successfully!")
            return redirect('car_list')
    else:
        form = CarForm()
    return render(request, 'cars/car_form.html', {'form': form})

@login_required
def car_update(request, pk):
    if not request.user.is_staff:
        messages.error(request, "Only admin can edit cars.")
        return redirect('car_list')
    
    car = get_object_or_404(Car, pk=pk)
    form = CarForm(request.POST or None, request.FILES or None, instance=car)
    if form.is_valid():
        form.save()
        messages.success(request, f"Car {car.brand} {car.name} updated successfully!")
        return redirect('car_list')
    return render(request, 'cars/car_form.html', {'form': form})

@login_required
def car_delete(request, pk):
    if not request.user.is_staff:
        messages.error(request, "Only admin can delete cars.")
        return redirect('car_list')
    
    car = get_object_or_404(Car, pk=pk, created_by=request.user)
    if request.method == 'POST':
        car.delete()
        messages.success(request, "Car deleted successfully!")
        return redirect('car_list')
    return render(request, 'cars/car_confirm_delete.html', {'car': car})

# --- User Reservations ---
@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'cars/my_reservations.html', {'reservations': reservations})

# --- Car Details ---
@login_required
def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    return render(request, 'cars/car_detail.html', {'car': car})
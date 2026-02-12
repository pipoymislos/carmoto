from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from datetime import date, datetime
from django.db.models import Sum, Q
from django.http import HttpResponse, FileResponse, JsonResponse
from django.template.loader import get_template
from django.conf import settings
from io import BytesIO
from .models import Car, Reservation, User
from .forms import CarForm, RegisterForm, ReservationForm
import json
from django.core import serializers

# Try to import xhtml2pdf, but handle gracefully if not installed
try:
    from xhtml2pdf import pisa
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: xhtml2pdf not installed. Receipt downloads will be disabled.")

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
    completed_reservations = Reservation.objects.filter(status='completed').count()
    cancelled_reservations = Reservation.objects.filter(status='cancelled').count()
    total_users = User.objects.filter(is_staff=False).count()
    
    # Revenue statistics
    total_revenue = Reservation.objects.filter(
        Q(status='approved') | Q(status='completed')
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
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
        'completed_reservations': completed_reservations,
        'cancelled_reservations': cancelled_reservations,
        'total_revenue': total_revenue,
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
    days = (reservation.end_date - reservation.start_date).days
    subtotal = reservation.car.price_per_day * days
    
    context = {
        'reservation': reservation,
        'days': days,
        'subtotal': subtotal
    }
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
    """
    Admin view to see all cars with filtering options
    """
    status_filter = request.GET.get('status', '')
    
    if status_filter == 'available':
        cars = Car.objects.filter(is_available=True).order_by('-created_at')
    elif status_filter == 'unavailable':
        cars = Car.objects.filter(is_available=False).order_by('-created_at')
    else:
        cars = Car.objects.all().order_by('-created_at')
    
    # Calculate stats
    cars_available = Car.objects.filter(is_available=True).count()
    
    context = {
        'cars': cars,
        'cars_available': cars_available,
        'status_filter': status_filter,
    }
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
            
            # Set default pickup/dropoff times if not provided
            if not reservation.pickup_time:
                reservation.pickup_time = "10:00:00"
            if not reservation.dropoff_time:
                reservation.dropoff_time = "10:00:00"
            
            # Calculate total amount
            reservation.total_amount = car.total_price(
                reservation.start_date, 
                reservation.end_date
            )
            reservation.status = 'pending'  # Default status
            reservation.save()
            
            messages.success(request, 
                f"Car {car.brand} {car.name} booked successfully! "
                f"Your reservation ID is #{reservation.id}. "
                f"We have sent a confirmation to {reservation.contact_email}. "
                f"Total amount: ₱{reservation.total_amount}")
            return redirect('my_reservations')  # Redirect to my_reservations after booking
    else:
        # Pre-fill email if user has one
        initial_data = {
            'contact_email': request.user.email if request.user.email else '',
        }
        form = ReservationForm(initial=initial_data)
    
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

# --- ENHANCED: User Reservations with Statistics and Receipts ---
# --- ENHANCED: User Reservations with Statistics and Receipts ---
@login_required
def my_reservations(request):
    """
    Enhanced view for users to see all their reservations with statistics
    """
    reservations = Reservation.objects.filter(
        customer=request.user
    ).select_related('car').order_by('-created_at')
    
    # Calculate rental days for each reservation
    for reservation in reservations:
        reservation.rental_days = (reservation.end_date - reservation.start_date).days
    
    # Calculate statistics
    pending_count = reservations.filter(status='pending').count()
    approved_count = reservations.filter(status='approved').count()
    total_count = reservations.count()
    
    # Calculate total spent (only approved/completed reservations)
    total_spent = reservations.filter(
        Q(status='approved') | Q(status='completed')
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'reservations': reservations,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'total_count': total_count,
        'total_spent': total_spent,
    }
    return render(request, 'cars/my_reservations.html', context)
@login_required
def reservation_detail(request, pk):
    """
    View reservation details for users
    """
    reservation = get_object_or_404(
        Reservation, 
        pk=pk, 
        customer=request.user
    )
    
    # Calculate days
    days = (reservation.end_date - reservation.start_date).days
    daily_rate = reservation.car.price_per_day
    subtotal = daily_rate * days
    
    context = {
        'reservation': reservation,
        'days': days,
        'daily_rate': daily_rate,
        'subtotal': subtotal,
        'today': date.today().isoformat(),  # Add today variable
    }
    return render(request, 'cars/reservation_detail.html', context)

# --- NEW: User Cancel Reservation ---
@login_required
def cancel_reservation(request, pk):
    """
    Allow users to cancel their pending reservations
    """
    reservation = get_object_or_404(
        Reservation, 
        pk=pk, 
        customer=request.user
    )
    
    # Only allow cancelling pending reservations
    if reservation.status == 'pending':
        reservation.status = 'cancelled'
        reservation.save()
        messages.success(request, f'Reservation #{reservation.id} cancelled successfully.')
    else:
        messages.error(request, 'Only pending reservations can be cancelled.')
    
    return redirect('my_reservations')

# --- NEW: Download Receipt for Users ---
@login_required
def download_receipt(request, pk):
    """
    Generate and download PDF receipt for approved/completed reservations
    """
    # Check if PDF support is available
    if not PDF_SUPPORT:
        messages.error(request, 'PDF generation is not available. Please install xhtml2pdf.')
        return redirect('my_reservations')
    
    reservation = get_object_or_404(
        Reservation, 
        pk=pk, 
        customer=request.user
    )
    
    # Only allow receipt download for approved or completed reservations
    if reservation.status not in ['approved', 'completed']:
        messages.error(request, 'Receipt is only available for approved or completed reservations.')
        return redirect('my_reservations')
    
    # Calculate rental details
    days = (reservation.end_date - reservation.start_date).days
    daily_rate = reservation.car.price_per_day
    subtotal = daily_rate * days
    
    # Get any additional fees (if your model has these fields)
    insurance_fee = getattr(reservation, 'insurance_fee', 0)
    extra_fees = getattr(reservation, 'extra_fees', 0)
    
    # Template context
    context = {
        'reservation': reservation,
        'days': days,
        'daily_rate': daily_rate,
        'subtotal': subtotal,
        'insurance_fee': insurance_fee,
        'extra_fees': extra_fees,
        'receipt_date': timezone.now(),
        'company_name': 'Car Moto',
        'company_address': '21 Metro Avenue, Manila, Philippines',
        'company_phone': '+63 (2) 8123 4567',
        'company_email': 'fleet@carmanager.ph',
        'company_vat': '123-456-789-000',
        'total_amount': reservation.total_amount,
    }
    
    # Render PDF
    template = get_template('cars/receipt_pdf.html')
    html = template.render(context)
    result = BytesIO()
    
    # Create PDF
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        # Generate filename
        filename = f'receipt_{reservation.id}_{reservation.customer.last_name}_{reservation.start_date.strftime("%Y%m%d")}.pdf'
        
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    messages.error(request, 'Error generating PDF receipt.')
    return redirect('my_reservations')

# --- NEW: Admin Download Receipt for Any Reservation ---
@staff_member_required
def admin_download_receipt(request, pk):
    """
    Admin version to download receipt for any reservation
    """
    if not PDF_SUPPORT:
        messages.error(request, 'PDF generation is not available.')
        return redirect('admin_dashboard')
    
    reservation = get_object_or_404(Reservation, pk=pk)
    
    # Calculate rental details
    days = (reservation.end_date - reservation.start_date).days
    daily_rate = reservation.car.price_per_day
    subtotal = daily_rate * days
    
    context = {
        'reservation': reservation,
        'days': days,
        'daily_rate': daily_rate,
        'subtotal': subtotal,
        'receipt_date': timezone.now(),
        'company_name': 'Car Moto',
        'company_address': '21 Metro Avenue, Manila, Philippines',
        'company_phone': '+63 (2) 8123 4567',
        'company_email': 'fleet@carmanager.ph',
        'company_vat': '123-456-789-000',
        'admin_download': True,
    }
    
    template = get_template('cars/receipt_pdf.html')
    html = template.render(context)
    result = BytesIO()
    
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        filename = f'receipt_admin_{reservation.id}_{reservation.customer.last_name}.pdf'
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    messages.error(request, 'Error generating PDF receipt.')
    return redirect('admin_dashboard')

# --- Car Details ---
@login_required
def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    return render(request, 'cars/car_detail.html', {'car': car})

# --- AJAX: Check Car Availability ---
@login_required
def check_availability(request):
    """
    AJAX endpoint to check if a car is available for given dates
    """
    car_id = request.GET.get('car_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    try:
        car = Car.objects.get(id=car_id)
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Check for conflicting reservations
        conflicting = Reservation.objects.filter(
            car=car,
            status__in=['pending', 'approved'],
            start_date__lte=end,
            end_date__gte=start
        ).exists()
        
        return JsonResponse({
            'available': not conflicting,
            'price_per_day': float(car.price_per_day),
            'total_days': (end - start).days,
            'total_price': float(car.total_price(start, end))
        })
    except (Car.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
from django.db import models
from django.contrib.auth.models import User
from datetime import date

class Car(models.Model):
    TRANSMISSION_CHOICES = [
        ('automatic', 'Automatic'),
        ('manual', 'Manual')
    ]
    
    FUEL_TYPE_CHOICES = [
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid')
    ]
    
    brand = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='car_images/', blank=True, null=True)
    description = models.TextField(blank=True)
    
    # New fields for car details
    transmission = models.CharField(
        max_length=20, 
        choices=TRANSMISSION_CHOICES, 
        default='automatic'
    )
    fuel_type = models.CharField(
        max_length=20, 
        choices=FUEL_TYPE_CHOICES, 
        default='gasoline'
    )
    seats = models.IntegerField(default=4)
    
    def __str__(self):
        return f"{self.brand} {self.name}"
    
    def total_days(self, start_date, end_date):
        return (end_date - start_date).days + 1
    
    def total_price(self, start_date, end_date):
        days = self.total_days(start_date, end_date)
        return days * self.price_per_day
    
    def get_transmission_display(self):
        """Get display name for transmission"""
        return dict(self.TRANSMISSION_CHOICES).get(self.transmission, self.transmission)
    
    def get_fuel_type_display(self):
        """Get display name for fuel type"""
        return dict(self.FUEL_TYPE_CHOICES).get(self.fuel_type, self.fuel_type)


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Payment Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded')
    ]
    
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Contact Information
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    
    # Booking Details
    start_date = models.DateField()
    end_date = models.DateField()
    pickup_time = models.TimeField(default='10:00')
    dropoff_time = models.TimeField(default='10:00')
    
    # Status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Payment Information
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Additional Info
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Reservation #{self.id} - {self.car} by {self.customer.username}"
    
    def save(self, *args, **kwargs):
        if self.start_date and self.end_date and self.car:
            self.total_amount = self.car.total_price(self.start_date, self.end_date)
        super().save(*args, **kwargs)
    
    def get_status_display(self):
        """Get display name for status"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
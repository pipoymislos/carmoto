# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Car, Reservation
from datetime import date

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['brand', 'name', 'description', 'price_per_day', 
                  'transmission', 'fuel_type', 'seats', 'image', 'is_available']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price_per_day': forms.NumberInput(attrs={'step': '0.01'}),
        }

class ReservationForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': date.today().isoformat()})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': date.today().isoformat()})
    )
    pickup_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    dropoff_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    
    class Meta:
        model = Reservation
        fields = ['contact_email', 'contact_phone', 'start_date', 'end_date', 
                  'pickup_time', 'dropoff_time', 'special_requests']
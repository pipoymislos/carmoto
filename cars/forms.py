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
    class Meta:
        model = Reservation
        fields = ['contact_email', 'contact_phone', 'start_date', 'end_date', 
                  'pickup_time', 'dropoff_time', 'special_requests']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'date-input'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'date-input'}),
            'pickup_time': forms.TimeInput(attrs={'type': 'time', 'class': 'time-input'}),
            'dropoff_time': forms.TimeInput(attrs={'type': 'time', 'class': 'time-input'}),
            'special_requests': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Any special requirements?'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'your@email.com'}),
            'contact_phone': forms.TextInput(attrs={'placeholder': '+63 XXX XXX XXXX'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date < date.today():
                raise forms.ValidationError("Start date cannot be in the past.")
            
            if end_date <= start_date:
                raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data
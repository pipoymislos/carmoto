from django.contrib import admin
from .models import Car, Reservation

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'name', 'price_per_day', 'is_available')
    list_filter = ('is_available', 'brand')
    search_fields = ('brand', 'name')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('car', 'customer', 'start_date', 'end_date', 'status')  # ✅ changed approved -> status
    list_filter = ('status',)  # ✅ changed approved -> status
    search_fields = ('car__name', 'customer__username')

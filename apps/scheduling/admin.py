from django.contrib import admin

from apps.scheduling.models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "date", "time_slot", "status")
    list_filter = ("date", "doctor", "status")
    search_fields = ("patient__full_name", "patient__phone", "doctor__first_name", "doctor__last_name")
    autocomplete_fields = ("patient", "doctor")

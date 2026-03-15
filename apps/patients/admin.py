from django.contrib import admin

from apps.patients.models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "date_of_birth", "created_at")
    search_fields = ("full_name", "phone", "email")

from django.contrib import admin

from apps.billing.models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("treatment_plan", "total_amount", "status", "issued_at")
    list_filter = ("status", "issued_at")
    search_fields = (
        "treatment_plan__appointment__patient__full_name",
        "treatment_plan__appointment__patient__phone",
    )

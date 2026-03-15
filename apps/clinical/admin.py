from django.contrib import admin

from apps.clinical.models import Service, Tooth, TreatmentPlan


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "estimated_duration")
    search_fields = ("name",)


@admin.register(Tooth)
class ToothAdmin(admin.ModelAdmin):
    list_display = ("patient", "tooth_number", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("patient__full_name", "patient__phone")


@admin.register(TreatmentPlan)
class TreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ("appointment", "status", "resulting_tooth_status", "completed_at")
    list_filter = ("status", "appointment__date", "appointment__doctor")
    search_fields = (
        "appointment__patient__full_name",
        "appointment__patient__phone",
        "appointment__doctor__first_name",
        "appointment__doctor__last_name",
    )
    filter_horizontal = ("teeth", "services")

from django.conf import settings
from django.db import models


class Service(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_duration = models.DurationField()
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ToothStatus(models.TextChoices):
    NORMAL = "normal", "Bình thường"
    CAVITY = "cavity", "Sâu răng"
    CROWN = "crown", "Răng sứ"
    MISSING = "missing", "Mất răng"
    TREATED = "treated", "Đã điều trị"


class Tooth(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="teeth")
    tooth_number = models.IntegerField()
    status = models.CharField(max_length=20, choices=ToothStatus.choices, default=ToothStatus.NORMAL)
    notes = models.CharField(max_length=255, blank=True)
    last_updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_teeth")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["patient", "tooth_number"]
        constraints = [
            models.UniqueConstraint(fields=["patient", "tooth_number"], name="uniq_patient_tooth"),
            models.CheckConstraint(
                condition=models.Q(tooth_number__gte=11, tooth_number__lte=48),
                name="tooth_number_between_11_48",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.patient.full_name} - R{self.tooth_number}"


class TreatmentPlanStatus(models.TextChoices):
    PLANNED = "planned", "Đã lên kế hoạch"
    IN_PROGRESS = "in_progress", "Đang thực hiện"
    COMPLETED = "completed", "Hoàn tất"


class TreatmentPlan(models.Model):
    appointment = models.OneToOneField("scheduling.Appointment", on_delete=models.CASCADE, related_name="treatment_plan")
    teeth = models.ManyToManyField(Tooth, related_name="treatment_plans", blank=True)
    services = models.ManyToManyField(Service, related_name="treatment_plans", blank=True)
    diagnosis = models.TextField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=TreatmentPlanStatus.choices, default=TreatmentPlanStatus.PLANNED)
    resulting_tooth_status = models.CharField(
        max_length=20,
        choices=ToothStatus.choices,
        default=ToothStatus.TREATED,
        help_text="Trạng thái sẽ được cập nhật cho các răng khi hoàn tất liệu trình.",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-appointment__date", "-appointment__time_slot"]

    def __str__(self) -> str:
        return f"TreatmentPlan #{self.pk} - {self.appointment.patient.full_name}"

    def sync_teeth_status(self) -> None:
        if self.status == TreatmentPlanStatus.COMPLETED:
            self.teeth.update(status=self.resulting_tooth_status)

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class AppointmentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Appointment(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_appointments",
        limit_choices_to={"role": "doctor"},
    )
    date = models.DateField()
    time_slot = models.TimeField()
    status = models.CharField(max_length=20, choices=AppointmentStatus.choices, default=AppointmentStatus.PENDING)
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "time_slot"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "date", "time_slot"],
                condition=Q(status=AppointmentStatus.CONFIRMED),
                name="uniq_confirmed_doctor_slot",
            )
        ]

    def clean(self) -> None:
        super().clean()
        conflicting = Appointment.objects.filter(
            doctor=self.doctor,
            date=self.date,
            time_slot=self.time_slot,
        ).exclude(pk=self.pk)

        if self.status == AppointmentStatus.CANCELLED:
            return

        if conflicting.exclude(status=AppointmentStatus.CANCELLED).exists():
            raise ValidationError(
                {"time_slot": "Bac si da co lich hen o khung gio nay."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.patient.full_name} - {self.doctor} @ {self.date} {self.time_slot}"

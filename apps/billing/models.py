from django.db import models


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Bản nháp"
    ISSUED = "issued", "Đã phát hành"
    PAID = "paid", "Đã thanh toán"


class Invoice(models.Model):
    treatment_plan = models.OneToOneField("clinical.TreatmentPlan", on_delete=models.CASCADE, related_name="invoice")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)
    issued_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self) -> str:
        return f"Invoice #{self.pk} - {self.treatment_plan.appointment.patient.full_name}"

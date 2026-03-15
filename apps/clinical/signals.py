from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.billing.models import Invoice
from apps.clinical.models import TreatmentPlan, TreatmentPlanStatus
from apps.scheduling.models import AppointmentStatus


def _sync_invoice(plan: TreatmentPlan) -> None:
    invoice, _ = Invoice.objects.get_or_create(treatment_plan=plan)
    invoice.total_amount = sum(service.price for service in plan.services.all())
    if plan.status == TreatmentPlanStatus.COMPLETED:
        invoice.status = "issued"
    invoice.save()


@receiver(post_save, sender=TreatmentPlan)
def treatment_plan_saved(sender, instance: TreatmentPlan, created: bool, **kwargs):
    if instance.status == TreatmentPlanStatus.COMPLETED and instance.completed_at is None:
        instance.completed_at = timezone.now()
        TreatmentPlan.objects.filter(pk=instance.pk).update(completed_at=instance.completed_at)
        instance.appointment.status = AppointmentStatus.COMPLETED
        instance.appointment.save(update_fields=["status"])

    instance.sync_teeth_status()
    _sync_invoice(instance)


@receiver(m2m_changed, sender=TreatmentPlan.teeth.through)
def treatment_plan_teeth_changed(sender, instance: TreatmentPlan, action: str, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        instance.sync_teeth_status()


@receiver(m2m_changed, sender=TreatmentPlan.services.through)
def treatment_plan_services_changed(sender, instance: TreatmentPlan, action: str, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        _sync_invoice(instance)

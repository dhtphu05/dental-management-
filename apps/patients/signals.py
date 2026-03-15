from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.clinical.models import Tooth
from apps.patients.models import Patient


TOOTH_NUMBERS = [
    11, 12, 13, 14, 15, 16, 17, 18,
    21, 22, 23, 24, 25, 26, 27, 28,
    31, 32, 33, 34, 35, 36, 37, 38,
    41, 42, 43, 44, 45, 46, 47, 48,
]


@receiver(post_save, sender=Patient)
def create_patient_teeth(sender, instance: Patient, created: bool, **kwargs):
    if not created:
        return

    Tooth.objects.bulk_create(
        [Tooth(patient=instance, tooth_number=number) for number in TOOTH_NUMBERS]
    )

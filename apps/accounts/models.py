from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "Quản trị viên"
    DOCTOR = "doctor", "Bác sĩ"
    RECEPTIONIST = "receptionist", "Lễ tân"
    PATIENT = "patient", "Bệnh nhân"


class CustomUser(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.PATIENT)
    phone = models.CharField(max_length=20, unique=True)

    def __str__(self) -> str:
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

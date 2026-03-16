from django import forms

from apps.accounts.models import CustomUser, UserRole
from apps.patients.models import Patient
from apps.scheduling.models import Appointment, AppointmentStatus


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "date", "time_slot", "status", "reason", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time_slot": forms.TimeInput(attrs={"type": "time"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class BookingAppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "date", "time_slot", "reason", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time_slot": forms.HiddenInput(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["time_slot"].required = True


class PublicBookingForm(forms.Form):
    full_name = forms.CharField(max_length=255, label="Họ và tên")
    phone = forms.CharField(max_length=20, label="Số điện thoại")
    doctor = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role=UserRole.DOCTOR).order_by("first_name", "last_name", "username"),
        label="Bác sĩ",
    )
    date = forms.DateField(label="Ngày khám", widget=forms.DateInput(attrs={"type": "date"}))
    time_slot = forms.TimeField(widget=forms.HiddenInput())
    reason = forms.CharField(max_length=255, required=False, label="Lý do khám")
    notes = forms.CharField(required=False, label="Ghi chú", widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["time_slot"].required = True

    def save(self):
        phone = self.cleaned_data["phone"].strip()
        patient, _ = Patient.objects.get_or_create(
            phone=phone,
            defaults={
                "full_name": self.cleaned_data["full_name"],
            },
        )
        patient.full_name = self.cleaned_data["full_name"]
        patient.save()

        appointment = Appointment.objects.create(
            patient=patient,
            doctor=self.cleaned_data["doctor"],
            date=self.cleaned_data["date"],
            time_slot=self.cleaned_data["time_slot"],
            reason=self.cleaned_data["reason"],
            notes=self.cleaned_data["notes"],
            status=AppointmentStatus.PENDING,
        )
        return appointment

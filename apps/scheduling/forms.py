from django import forms

from apps.scheduling.models import Appointment


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

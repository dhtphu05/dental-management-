from datetime import date, time
import re

from django import forms
from django.db.models import Q

from apps.accounts.models import CustomUser, UserRole
from apps.patients.models import Patient
from apps.scheduling.models import Appointment, AppointmentStatus


PUBLIC_BOOKING_SLOT_TIMES = {
    time(8, 0), time(8, 30), time(9, 0), time(9, 30),
    time(10, 0), time(10, 30), time(13, 0), time(13, 30),
    time(14, 0), time(14, 30), time(15, 0), time(15, 30),
}


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "date", "time_slot", "status", "reason", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time_slot": forms.TimeInput(attrs={"type": "time"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "patient": "Bệnh nhân",
            "doctor": "Bác sĩ",
            "date": "Ngày khám",
            "time_slot": "Khung giờ",
            "status": "Trạng thái",
            "reason": "Lý do khám",
            "notes": "Ghi chú",
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
        labels = {
            "patient": "Bệnh nhân",
            "doctor": "Bác sĩ",
            "date": "Ngày khám",
            "time_slot": "Khung giờ",
            "reason": "Lý do khám",
            "notes": "Ghi chú",
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
        required=False,
        empty_label="Bất kỳ bác sĩ phù hợp",
    )
    date = forms.DateField(label="Ngày khám", widget=forms.DateInput(attrs={"type": "date"}))
    time_slot = forms.TimeField(widget=forms.HiddenInput())
    reason = forms.CharField(max_length=255, required=False, label="Lý do khám")
    notes = forms.CharField(required=False, label="Ghi chú", widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["time_slot"].required = True
        self.resolved_doctor = None

    def clean_full_name(self):
        full_name = " ".join(self.cleaned_data["full_name"].split())
        if len(full_name) < 2:
            raise forms.ValidationError("Họ và tên phải có ít nhất 2 ký tự.")
        return full_name

    def clean_phone(self):
        phone = re.sub(r"\s+", "", self.cleaned_data["phone"])
        if not re.fullmatch(r"0\d{9,10}", phone):
            raise forms.ValidationError("Số điện thoại không hợp lệ. Vui lòng nhập số bắt đầu bằng 0 và có 10-11 chữ số.")
        return phone

    def clean_date(self):
        appointment_date = self.cleaned_data["date"]
        if appointment_date < date.today():
            raise forms.ValidationError("Không thể đặt lịch cho ngày trong quá khứ.")
        return appointment_date

    def clean_time_slot(self):
        slot = self.cleaned_data["time_slot"]
        if slot not in PUBLIC_BOOKING_SLOT_TIMES:
            raise forms.ValidationError("Khung giờ đã chọn không hợp lệ.")
        return slot

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get("doctor")
        appointment_date = cleaned_data.get("date")
        slot = cleaned_data.get("time_slot")

        if not all([appointment_date, slot]):
            return cleaned_data

        if doctor:
            conflict_exists = Appointment.objects.exclude(status=AppointmentStatus.CANCELLED).filter(
                doctor=doctor,
                date=appointment_date,
                time_slot=slot,
            ).exists()
            if conflict_exists:
                self.add_error("time_slot", "Khung giờ này đã có người đặt. Vui lòng chọn giờ khác.")
            else:
                self.resolved_doctor = doctor
            return cleaned_data

        available_doctor = (
            self.fields["doctor"].queryset.exclude(
                Q(doctor_appointments__date=appointment_date)
                & Q(doctor_appointments__time_slot=slot)
                & ~Q(doctor_appointments__status=AppointmentStatus.CANCELLED)
            )
            .first()
        )
        if not available_doctor:
            self.add_error("time_slot", "Khung giờ này hiện không còn bác sĩ trống. Vui lòng chọn giờ khác.")
        else:
            self.resolved_doctor = available_doctor

        return cleaned_data

    def save(self):
        phone = self.cleaned_data["phone"]
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
            doctor=self.resolved_doctor or self.cleaned_data["doctor"],
            date=self.cleaned_data["date"],
            time_slot=self.cleaned_data["time_slot"],
            reason=self.cleaned_data["reason"],
            notes=self.cleaned_data["notes"],
            status=AppointmentStatus.PENDING,
        )
        return appointment

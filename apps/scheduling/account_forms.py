from django import forms
from django.core.exceptions import ValidationError

from apps.accounts.models import CustomUser, UserRole
from apps.patients.models import Patient


class BookingAccountCreateForm(forms.Form):
    phone = forms.CharField(label="Số điện thoại", disabled=True, required=False)
    password1 = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput(render_value=True), min_length=8)
    password2 = forms.CharField(label="Nhập lại mật khẩu", widget=forms.PasswordInput(render_value=True), min_length=8)

    def __init__(self, *args, patient: Patient, **kwargs):
        super().__init__(*args, **kwargs)
        self.patient = patient
        self.fields["phone"].initial = patient.phone

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            self.add_error("password2", "Mật khẩu xác nhận không khớp.")
        if self.patient.user_id:
            raise ValidationError("Hồ sơ này đã có tài khoản.")
        if CustomUser.objects.filter(phone=self.patient.phone).exists():
            raise ValidationError("Số điện thoại này đã có tài khoản.")
        return cleaned_data

    def save(self):
        user = CustomUser.objects.create_user(
            username=self.patient.phone,
            password=self.cleaned_data["password1"],
            phone=self.patient.phone,
            role=UserRole.PATIENT,
            first_name=self.patient.full_name,
        )
        self.patient.user = user
        self.patient.save(update_fields=["user"])
        return user

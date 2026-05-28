import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.accounts.models import UserRole
from apps.patients.models import Patient


User = get_user_model()


class MixedAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Tên đăng nhập / Số điện thoại")
    password = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput)

    error_messages = {
        "invalid_login": "Tên đăng nhập, số điện thoại hoặc mật khẩu không đúng.",
        "inactive": "Tài khoản này đã bị vô hiệu hóa.",
    }


class PatientRegistrationForm(forms.Form):
    full_name = forms.CharField(
        max_length=255,
        label="Họ và tên",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ví dụ: Đoàn Hoàng Thiên Phú",
                "autocomplete": "name",
                "maxlength": "255",
            }
        ),
    )
    phone = forms.CharField(
        max_length=20,
        label="Số điện thoại",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Nhập số điện thoại của bạn",
                "autocomplete": "tel",
                "inputmode": "numeric",
                "maxlength": "11",
                "pattern": "0[0-9]{9,10}",
            }
        ),
    )
    password1 = forms.CharField(
        label="Mật khẩu",
        strip=False,
        help_text="Tối thiểu 8 ký tự, nên gồm chữ hoa, chữ thường và số.",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Tạo mật khẩu",
                "autocomplete": "new-password",
                "minlength": "8",
            }
        ),
    )
    password2 = forms.CharField(
        label="Nhập lại mật khẩu",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Nhập lại mật khẩu",
                "autocomplete": "new-password",
                "minlength": "8",
            }
        ),
    )

    def clean_full_name(self):
        full_name = " ".join((self.cleaned_data.get("full_name") or "").split())
        if len(full_name) < 2:
            raise forms.ValidationError("Họ và tên phải có ít nhất 2 ký tự.")
        if not re.fullmatch(r"[A-Za-zÀ-ỹ\s'.-]+", full_name):
            raise forms.ValidationError("Họ và tên chỉ được chứa chữ cái và khoảng trắng hợp lệ.")
        if len(full_name.replace(" ", "")) < 4:
            raise forms.ValidationError("Vui lòng nhập họ và tên đầy đủ hơn.")
        return full_name

    def clean_phone(self):
        phone = re.sub(r"\s+", "", self.cleaned_data.get("phone") or "")
        if not phone.isdigit():
            raise forms.ValidationError("Số điện thoại chỉ được chứa chữ số.")

        if not re.fullmatch(r"0\d{9}", phone):
            raise forms.ValidationError("Số điện thoại không hợp lệ. Vui lòng nhập số bắt đầu bằng 0 và có đúng 10 chữ số.")

        if User.objects.filter(username=phone).exclude(role=UserRole.PATIENT).exists():
            raise forms.ValidationError("Số điện thoại này đang xung đột với tài khoản nội bộ.")

        if User.objects.filter(phone=phone).exclude(role=UserRole.PATIENT).exists():
            raise forms.ValidationError("Số điện thoại này đang được dùng cho tài khoản nội bộ.")

        if User.objects.filter(phone=phone, role=UserRole.PATIENT).exists():
            raise forms.ValidationError("Số điện thoại này đã có tài khoản bệnh nhân.")

        return phone

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        phone = cleaned_data.get("phone")
        full_name = cleaned_data.get("full_name")

        if password1:
            try:
                validate_password(
                    password1,
                    user=User(
                        username=phone or "",
                        phone=phone or "",
                        first_name=full_name or "",
                        role=UserRole.PATIENT,
                    ),
                )
            except ValidationError as exc:
                for message in exc.messages:
                    self.add_error("password1", message)

            if password1.isdigit():
                self.add_error("password1", "Mật khẩu không được chỉ gồm chữ số.")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Mật khẩu nhập lại không khớp.")

        return cleaned_data

    def save(self):
        full_name = self.cleaned_data["full_name"]
        phone = self.cleaned_data["phone"]
        password = self.cleaned_data["password1"]

        user = User.objects.create_user(
            username=phone,
            phone=phone,
            first_name=full_name,
            last_name="",
            role=UserRole.PATIENT,
            password=password,
        )

        patient, _ = Patient.objects.get_or_create(
            phone=phone,
            defaults={"full_name": full_name},
        )
        patient.full_name = full_name
        patient.user = user
        patient.save()
        return user

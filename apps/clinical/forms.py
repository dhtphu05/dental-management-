import json
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django import forms

from apps.clinical.models import Service, Tooth, ToothStatus, TreatmentPlan


class ServiceForm(forms.ModelForm):
    duration_minutes = forms.IntegerField(
        label="Thời gian thực hiện",
        min_value=5,
        max_value=480,
        help_text="Nhập theo phút, ví dụ 30 hoặc 90.",
        widget=forms.NumberInput(
            attrs={
                "placeholder": "Ví dụ: 45",
                "min": "5",
                "max": "480",
                "step": "5",
                "inputmode": "numeric",
            }
        ),
    )

    class Meta:
        model = Service
        fields = ["name", "price", "duration_minutes", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ví dụ: Cạo vôi và đánh bóng"}),
            "price": forms.NumberInput(
                attrs={
                    "placeholder": "Ví dụ: 300000",
                    "min": "1000",
                    "step": "1000",
                    "inputmode": "numeric",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Mô tả ngắn về dịch vụ, chỉ định hoặc những gì bệnh nhân cần biết.",
                }
            ),
        }
        labels = {
            "name": "Tên dịch vụ",
            "price": "Giá tiền",
            "description": "Mô tả",
        }
        help_texts = {
            "price": "Nhập số tiền theo VNĐ, không cần dấu chấm hay ký hiệu tiền tệ.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.estimated_duration:
            total_minutes = int(self.instance.estimated_duration.total_seconds() // 60)
            self.fields["duration_minutes"].initial = total_minutes

    def clean_name(self):
        name = " ".join((self.cleaned_data.get("name") or "").split())
        if len(name) < 3:
            raise forms.ValidationError("Tên dịch vụ cần có ít nhất 3 ký tự.")

        queryset = Service.objects.filter(name__iexact=name)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("Tên dịch vụ này đã tồn tại.")
        return name

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is None:
            raise forms.ValidationError("Vui lòng nhập giá dịch vụ.")

        try:
            normalized = Decimal(price)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise forms.ValidationError("Giá dịch vụ không hợp lệ.") from exc

        if normalized <= 0:
            raise forms.ValidationError("Giá dịch vụ phải lớn hơn 0.")
        if normalized < Decimal("1000"):
            raise forms.ValidationError("Giá dịch vụ tối thiểu là 1.000 VNĐ.")
        if normalized > Decimal("100000000"):
            raise forms.ValidationError("Giá dịch vụ đang vượt quá giới hạn cho phép.")
        return normalized.quantize(Decimal("0.01"))

    def clean_duration_minutes(self):
        duration_minutes = self.cleaned_data.get("duration_minutes")
        if duration_minutes is None:
            raise forms.ValidationError("Vui lòng nhập thời gian thực hiện.")
        if duration_minutes < 5:
            raise forms.ValidationError("Thời gian thực hiện tối thiểu là 5 phút.")
        if duration_minutes > 480:
            raise forms.ValidationError("Thời gian thực hiện không được vượt quá 480 phút.")
        return duration_minutes

    def clean_description(self):
        description = " ".join((self.cleaned_data.get("description") or "").split())
        if description and len(description) < 10:
            raise forms.ValidationError("Mô tả nên có ít nhất 10 ký tự hoặc để trống.")
        return description

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.estimated_duration = timedelta(minutes=self.cleaned_data["duration_minutes"])
        if commit:
            instance.save()
        return instance


class TreatmentPlanForm(forms.ModelForm):
    teeth = forms.ModelMultipleChoiceField(
        queryset=Tooth.objects.none(),
        widget=forms.MultipleHiddenInput,
        required=False,
    )
    tooth_states = forms.CharField(widget=forms.HiddenInput, required=False)
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = TreatmentPlan
        fields = ["diagnosis", "notes", "status", "resulting_tooth_status", "teeth", "tooth_states", "services"]
        widgets = {
            "diagnosis": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "diagnosis": "Chẩn đoán",
            "notes": "Ghi chú",
            "status": "Trạng thái liệu trình",
            "resulting_tooth_status": "Trạng thái răng sau điều trị",
            "services": "Dịch vụ thực hiện",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["services"].label = "Dịch vụ thực hiện"
        appointment = self.instance.appointment if self.instance.pk else None
        if appointment:
            self.fields["teeth"].queryset = Tooth.objects.filter(
                patient=appointment.patient,
                tooth_number__gte=11,
                tooth_number__lte=48,
            ).order_by("tooth_number")
            self.initial.setdefault(
                "tooth_states",
                json.dumps(
                    {
                        str(tooth.pk): tooth.status
                        for tooth in self.fields["teeth"].queryset
                    }
                ),
            )

    def clean_tooth_states(self):
        raw_value = self.cleaned_data.get("tooth_states") or "{}"
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError("Dữ liệu sơ đồ răng không hợp lệ.") from exc

        valid_statuses = {choice for choice, _ in ToothStatus.choices}
        valid_ids = {str(tooth.pk) for tooth in self.fields["teeth"].queryset}

        sanitized = {}
        for tooth_id, status in parsed.items():
            if tooth_id in valid_ids and status in valid_statuses:
                sanitized[tooth_id] = status

        return sanitized

    def save(self, commit=True):
        tooth_states = self.cleaned_data.get("tooth_states", {})
        instance = super().save(commit)

        if tooth_states:
            selected_ids = [int(tooth_id) for tooth_id, status in tooth_states.items() if status != ToothStatus.NORMAL]
            self.cleaned_data["teeth"] = self.fields["teeth"].queryset.filter(pk__in=selected_ids)
            instance.teeth.set(self.cleaned_data["teeth"])
            for tooth in self.fields["teeth"].queryset:
                new_status = tooth_states.get(str(tooth.pk), ToothStatus.NORMAL)
                if tooth.status != new_status:
                    tooth.status = new_status
                    tooth.save(update_fields=["status", "updated_at"])

        return instance

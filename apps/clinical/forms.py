import json

from django import forms

from apps.clinical.models import Service, Tooth, ToothStatus, TreatmentPlan


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "price", "estimated_duration", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "name": "Tên dịch vụ",
            "price": "Giá tiền",
            "estimated_duration": "Thời gian ước tính",
            "description": "Mô tả",
        }


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

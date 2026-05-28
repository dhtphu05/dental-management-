with open("apps/scheduling/forms.py", "r") as f:
    text = f.read()

new_form = """
class SidebarAppointmentForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=20, 
        label="Số điện thoại Bệnh nhân", 
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Nhập SĐT để tìm hoặc tạo mới", "class": "form-input"}),
        help_text="Nhập SĐT, sau đó nhấn Tìm kiếm hoặc focus ra ngoài"
    )
    full_name = forms.CharField(
        max_length=255, 
        label="Họ và tên Bệnh nhân", 
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Tên bệnh nhân", "class": "form-input"})
    )

    class Meta:
        model = Appointment
        fields = ["doctor", "date", "time_slot", "status", "reason", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time_slot": forms.TimeInput(attrs={"type": "time"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "doctor": "Bác sĩ",
            "date": "Ngày khám",
            "time_slot": "Khung giờ",
            "status": "Trạng thái",
            "reason": "Lý do khám",
            "notes": "Ghi chú",
        }

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        import re
        phone = re.sub(r"\s+", "", phone)
        if not re.fullmatch(r"0\d{9,10}", phone):
            raise forms.ValidationError("SĐT không hợp lệ (Bắt đầu bằng 0, gồm 10-11 số).")
        return phone

    def save(self, commit=True):
        phone = self.cleaned_data["phone"]
        full_name = self.cleaned_data["full_name"]
        
        # Get or create patient. Note: if patient exists, we just link it.
        # If the user intentionally changes the name, we update it.
        patient, created = Patient.objects.get_or_create(
            phone=phone,
            defaults={"full_name": full_name}
        )
        if not created and patient.full_name != full_name:
            patient.full_name = full_name
            patient.save()
            
        instance = super().save(commit=False)
        instance.patient = patient
        if commit:
            instance.save()
        return instance
"""

if "SidebarAppointmentForm" not in text:
    text = text + "\n" + new_form

with open("apps/scheduling/forms.py", "w") as f:
    f.write(text)

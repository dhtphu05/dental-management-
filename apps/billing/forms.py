from django import forms

from apps.billing.models import Invoice


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["status"]
        labels = {
            "status": "Trạng thái hóa đơn",
        }

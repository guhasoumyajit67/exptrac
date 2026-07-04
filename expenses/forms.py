from django import forms
from django.db.models import Q
import os
from .models import (
    Category,
    Item,
    Payer,
    Transaction,
)

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        # 🚨 UPDATED: Added 'unit' so users can choose a unit type when creating items manually
        fields = ['name', 'category', 'unit']


class PayerForm(forms.ModelForm):
    class Meta:
        model = Payer
        fields = ['name', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        # 🚨 FIXED: Removed 'unit' from this list since it now lives on the Item model
        fields = ["date", "item", "price", "quantity", "payer", "comment"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "comment": forms.Textarea(attrs={"rows": 2}),  # Kept short and neat
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # 1. APPLY STYLE CLASSES TO EVERY FIELD
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.RadioSelect)):
                field.widget.attrs["class"] = "form-select form-select-sm"
            else:
                field.widget.attrs["class"] = "form-control form-control-sm"

        # 2. Keep your user queries locked down safely
        if self.user:
            self.fields["item"].queryset = Item.objects.filter(
                Q(user__isnull=True) | Q(user=self.user)
            )
            self.fields["payer"].queryset = Payer.objects.filter(user=self.user)






class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        label="Select Excel File",
        help_text="Upload a spreadsheet containing your transaction logs."
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ['.xlsx', '.xls']:
            raise forms.ValidationError("Unsupported file format! Please upload a valid Excel spreadsheet (.xlsx or .xls).")
        return file
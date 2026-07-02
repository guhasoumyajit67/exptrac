from django import forms
from django.db.models import Q
from .models import (
    Category,
    Item,
    Payer,
    Transaction,
)

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        # Regular users only provide the name and assign it to a global category
        fields = ['name', 'category']

class PayerForm(forms.ModelForm):
    class Meta:
        model = Payer
        fields = ['name', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

# Inside your expenses/forms.py
class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["date", "item", "price", "quantity", "unit", "payer", "comment"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "comment": forms.Textarea(attrs={"rows": 2}),  # Kept short and neat
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # 1. APPLY NATIVE BOOTSTRAP CLASSES TO EVERY FIELD
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
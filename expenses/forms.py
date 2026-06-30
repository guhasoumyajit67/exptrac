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
            'color': forms.Input(attrs={'type': 'color'}),
        }

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["date", "item", "payer", "amount", "comment"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "comment": forms.Textarea(attrs={"rows": 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields["item"].queryset = Item.objects.filter(
                Q(user__isnull=True) | Q(user=self.user)
            )
            self.fields["payer"].queryset = Payer.objects.filter(user=self.user)
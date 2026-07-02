from django.views.generic.edit import CreateView
from django.views.generic import ListView,TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from .models import (
    Transaction,
    Item,
    Payer,
)
from .forms import (
    TransactionForm,
    ItemForm,
    PayerForm,
)

class HomePageView(TemplateView):
    template_name = "home.html"

class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transaction_form.html"
    success_url = reverse_lazy("create_transaction")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        initial_date = timezone.now().date()
        initial_payer = None

        last_transaction = (
            Transaction.objects.filter(user=self.request.user)
            .order_by("-id")
            .first()
        )
        if last_transaction:
            initial_date = last_transaction.date
            initial_payer = last_transaction.payer

        initial["date"] = initial_date

        if initial_payer:
            initial["payer"] = initial_payer

        return initial
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    

class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transaction_list.html"
    context_object_name = "transactions"

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-date', '-id')
    

class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "item_form.html"
    success_url = reverse_lazy("create_transaction")

    def form_valid(self, form):
        """Securely attach the logged-in user to this custom item row."""
        form.instance.user = self.request.user
        return super().form_valid(form)
    

class PayerCreateView(LoginRequiredMixin, CreateView):
    model = Payer
    form_class = PayerForm
    template_name = "payer_form.html"
    success_url = reverse_lazy("create_transaction")

    def form_valid(self, form):
        """Securely attach the logged-in user to this new payer profile."""
        form.instance.user = self.request.user
        return super().form_valid(form)
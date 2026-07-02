from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from django.db.models import Sum
from .models import Transaction, Item, Payer
from .forms import TransactionForm, ItemForm, PayerForm
from django.contrib import messages

class HomePageView(TemplateView):
    template_name = "home.html"


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transaction_list.html"
    context_object_name = "transactions"

    def get_queryset(self):
        """
        Optimized with select_related to prevent N+1 queries when loading items & categories.
        """
        return (
            Transaction.objects.filter(user=self.request.user)
            .select_related("item__category", "payer")
            .order_by("-date", "-id")
        )
    


class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transaction_form.html"
    
    # 1. REDIRECT BACK TO SELF: Keeps the form open for back-to-back logs
    success_url = reverse_lazy("create_transaction")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        initial_date = timezone.now().date()
        initial_payer = None

        # Your sticky logic shines here! It grabs the row you *just* saved
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
        
        # 2. SUCCESS FEEDBACK: Gives a subtle confirmation that entry went through
        messages.success(
            self.request, 
            f"Successfully logged '{form.instance.item.name}' for ₹{form.instance.price}!"
        )
        
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transaction_form.html"
    success_url = reverse_lazy("transaction_list")

    def get_queryset(self):
        """Security: Prevents users from manually altering primary key strings in forms or URLs."""
        return Transaction.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        """Passes user argument initialization context into your form during the edit save request lifecycle."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = "transaction_confirm_delete.html"
    success_url = reverse_lazy("transaction_list")

    def get_queryset(self):
        """Security: Only allow a user to drop transaction record instances they completely own."""
        return Transaction.objects.filter(user=self.request.user)


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "item_form.html"
    success_url = reverse_lazy("create_transaction")

    def form_valid(self, form):
        """Securely ties custom created unique items straight to this user footprint profile."""
        form.instance.user = self.request.user
        return super().form_valid(form)
    

class PayerCreateView(LoginRequiredMixin, CreateView):
    model = Payer
    form_class = PayerForm
    template_name = "payer_form.html"
    success_url = reverse_lazy("create_transaction")

    def form_valid(self, form):
        """Securely logs the dashboard payer account instance directly into the user relational map."""
        form.instance.user = self.request.user
        return super().form_valid(form)
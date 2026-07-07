from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import ProtectedError, Count
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.contrib import messages
from django.views import View
import openpyxl
import re

from .models import Transaction, Item, Payer, Category
from .forms import TransactionForm, ItemForm, PayerForm, ExcelUploadForm




class HomePageView(TemplateView):
    template_name = "home.html"





# ==============================================================================
# TRANSACTION VIEWS
# ==============================================================================

class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "expenses/transaction_form.html"
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
        messages.success(
            self.request, 
            f"Successfully logged '{form.instance.item.name}' for ₹{form.instance.price}!"
        )
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "expenses/transaction_form.html"
    success_url = reverse_lazy("transaction_list")

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = "expenses/transaction_confirm_delete.html"
    success_url = reverse_lazy("transaction_list")

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    

class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "expenses/transaction_list.html"
    context_object_name = "transactions"

    def get_queryset(self):
        return (
            Transaction.objects.filter(user=self.request.user)
            .select_related("item__category", "payer")
            .order_by("-date", "-id")
        )








# ==============================================================================
# ITEM VIEWS
# ==============================================================================

class ItemManagementListView(LoginRequiredMixin, ListView):
    model = Item
    template_name = "expenses/manage_items.html"
    context_object_name = "items"

    def get_queryset(self):
        # 🚨 FIX: Add select_related for performance and annotate with transaction counts
        return Item.objects.filter(user=self.request.user)\
                           .select_related('category')\
                           .annotate(transaction_count=Count('transaction'))\
                           .order_by('name')




class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "expenses/item_form.html"

    # 🚨 THE FIX: Dynamically determine where to route on completion
    def get_success_url(self):
        # Checks if 'next' is passed in either the GET query string or POST payload body
        redirect_to = self.request.GET.get('next') or self.request.POST.get('next')
        if redirect_to:
            return redirect_to
        # Fallback to transaction form if no 'next' is declared
        return reverse_lazy("create_transaction")

    def form_valid(self, form):
        item_name = form.cleaned_data.get('name')
        if Item.objects.filter(user=self.request.user, name__iexact=item_name).exists():
            form.add_error('name', f'You have already created a custom item named "{item_name}".')
            return self.form_invalid(form)
            
        form.instance.user = self.request.user
        return super().form_valid(form)


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = "expenses/item_form.html"

    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)

    # 🚨 FIX: Read the 'next' parameter from the URL query string on edit success
    def get_success_url(self):
        redirect_to = self.request.GET.get('next') or self.request.POST.get('next')
        if redirect_to:
            return redirect_to
        return reverse_lazy("manage_items")
    

class ItemDeleteView(LoginRequiredMixin, DeleteView):
    model = Item
    template_name = "expenses/item_confirm_delete.html"

    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        item_name = self.object.name
        redirect_to = request.POST.get('next')
        fallback_url = redirect_to if redirect_to else reverse("manage_items")
        
        try:
            self.object.delete()
            messages.success(request, f"Success! Item '{item_name}' has been safely removed.")
            return redirect(fallback_url)
        except ProtectedError:
            messages.error(
                request, 
                f"Cannot delete item '{item_name}' because it is currently tracked inside active ledger logs!"
            )
            return redirect(fallback_url)








# ==============================================================================
# PAYER VIEWS
# ==============================================================================

class PayerManagementListView(LoginRequiredMixin, ListView):
    model = Payer
    template_name = "expenses/manage_payers.html"
    context_object_name = "payers"

    def get_queryset(self):
        return (
            Payer.objects.filter(user=self.request.user)
            .annotate(transaction_count=Count('transaction'))
            .order_by('name')
        )


class PayerCreateView(LoginRequiredMixin, CreateView):
    model = Payer
    form_class = PayerForm
    template_name = "expenses/payer_form.html"

    def get(self, request, *args, **kwargs):
        referer = request.META.get('HTTP_REFERER')
        if referer:
            request.session['payer_form_origin_url'] = referer
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.session.pop('payer_form_origin_url', reverse("manage_payers"))

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class PayerUpdateView(LoginRequiredMixin, UpdateView):
    model = Payer
    form_class = PayerForm
    template_name = "expenses/payer_form.html"

    def get_queryset(self):
        return Payer.objects.filter(user=self.request.user)

    # 🚨 FIX: Read the 'next' parameter from the URL query string on edit success
    def get_success_url(self):
        redirect_to = self.request.GET.get('next') or self.request.POST.get('next')
        if redirect_to:
            return redirect_to
        return reverse_lazy("manage_payers")


class PayerDeleteView(LoginRequiredMixin, DeleteView):
    model = Payer
    template_name = "expenses/payer_confirm_delete.html"

    def get_queryset(self):
        return Payer.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        payer_name = self.object.name
        
        redirect_to = request.POST.get('next')
        fallback_url = redirect_to if redirect_to else reverse("manage_payers")
        
        try:
            self.object.delete()
            messages.success(request, f"Success! Payer '{payer_name}' has been safely removed.")
            # 🚨 THIS NOW CORRECTLY USES THE FALLBACK_URL ON SUCCESSFUL DELETION TOO
            return redirect(fallback_url)
            
        except ProtectedError:
            messages.error(
                request, 
                f"Cannot delete payer '{payer_name}' because they are currently tied to existing transactions in your ledger."
            )
            return redirect(fallback_url)










# ==============================================================================
# BULK OPERATIONS VIEWS
# ==============================================================================

class TransactionBulkUploadView(LoginRequiredMixin, FormView):
    form_class = ExcelUploadForm
    template_name = "expenses/bulk_upload.html"
    success_url = reverse_lazy("transaction_list")

    def form_valid(self, form):
        excel_file = self.request.FILES['excel_file']
        wb = openpyxl.load_workbook(excel_file, data_only=True)
        sheet = wb.active
        
        item_cache = {item.name.strip().lower(): item for item in Item.objects.all()}
        payer_cache = {payer.name.strip().lower(): payer for payer in Payer.objects.filter(user=self.request.user)}
        
        transactions_to_create = []
        pending_review_rows = []

        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if not row or row[0] is None:
                continue
                
            date_val, item_str, price_raw, quantity_raw, payer_str, comment_val = row[:6]
            item_raw_name = str(item_str).strip() if item_str else ""
            payer_raw_name = str(payer_str).strip() if payer_str else ""

            final_price = 0.0
            if price_raw is not None:
                price_digits = re.sub(r'[^\d.]', '', str(price_raw))
                final_price = float(price_digits) if price_digits else 0.0

            final_quantity = None
            if quantity_raw is not None and str(quantity_raw).strip():
                qty_match = re.search(r'\d+(\.\d+)?', str(quantity_raw))
                if qty_match:
                    qty_float = float(qty_match.group())
                    final_quantity = int(qty_float) if qty_float.is_integer() else qty_float

            item_obj = item_cache.get(item_raw_name.lower())
            payer_obj = payer_cache.get(payer_raw_name.lower())

            date_str = date_val.strftime('%Y-%m-%d') if hasattr(date_val, 'strftime') else str(date_val)

            row_data = {
                'row_idx': row_idx,
                'date': date_str,
                'item_name': item_raw_name,
                'price': final_price,
                'quantity': final_quantity,
                'payer_name': payer_raw_name,
                'comment': str(comment_val).strip() if comment_val else ""
            }

            if item_obj and payer_obj:
                row_data['item_id'] = item_obj.id
                row_data['payer_id'] = payer_obj.id
                transactions_to_create.append(row_data)
            else:
                if item_obj:
                    row_data['item_id'] = item_obj.id
                if payer_obj:
                    row_data['payer_id'] = payer_obj.id
                
                if not item_obj:
                    row_data['error'] = "Missing Item"
                elif not payer_obj:
                    row_data['error'] = "Missing Payer"
                    
                pending_review_rows.append(row_data)

        self.request.session['bulk_upload_valid_rows'] = transactions_to_create
        self.request.session['bulk_upload_review_rows'] = pending_review_rows

        if pending_review_rows:
            return redirect('bulk_upload_review')
            
        return redirect('bulk_upload_confirm_commit')


class TransactionBulkReviewView(LoginRequiredMixin, View):
    template_name = "expenses/bulk_review.html"

    def get(self, request, *args, **kwargs):
        review_rows = request.session.get('bulk_upload_review_rows', [])
        valid_rows = request.session.get('bulk_upload_valid_rows', [])
        
        if not review_rows and not valid_rows:
            messages.info(request, "No transaction staging queue found. Please upload a spreadsheet first.")
            return redirect('bulk_upload_transactions')

        missing_items = []
        for row in review_rows:
            name = row.get('item_name')
            if name and not row.get('item_id'):
                cleaned_name = name.strip()
                if cleaned_name not in missing_items:
                    missing_items.append(cleaned_name)
                    
        missing_items = sorted(missing_items)
        all_items = Item.objects.all().order_by('name')
        all_categories = Category.objects.all().order_by('name')

        context = {
            'missing_items': missing_items,
            'review_rows_count': len(review_rows),
            'valid_rows_count': len(valid_rows),
            'all_items': all_items,
            'all_categories': all_categories,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        review_rows = request.session.get('bulk_upload_review_rows', [])
        valid_rows = request.session.get('bulk_upload_valid_rows', [])
        target_item_name = request.POST.get('target_item_name')
        
        if target_item_name:
            target_item_name = target_item_name.strip()

        if action == "create_custom":
            category_id = request.POST.get('category_id')
            unit_value = request.POST.get('unit')
            category_obj = Category.objects.get(id=category_id)
            
            if Item.objects.filter(user=request.user, name__iexact=target_item_name).exists():
                messages.error(request, f"You already have a custom item named '{target_item_name}'. Use 'Map to Existing' instead.")
                return redirect('bulk_upload_review')

            new_custom_item, created = Item.objects.get_or_create(
                name=target_item_name,
                user=request.user,
                defaults={
                    'category': category_obj,
                    'unit': unit_value
                }
            )

            updated_review_rows = []
            for row in review_rows:
                row_name = row.get('item_name', '').strip() if row.get('item_name') else ''
                if row_name == target_item_name:
                    row['item_id'] = new_custom_item.id
                    row.pop('error', None)  
                    valid_rows.append(row)
                else:
                    updated_review_rows.append(row)
            
            review_rows = updated_review_rows
            request.session['bulk_upload_review_rows'] = review_rows
            request.session['bulk_upload_valid_rows'] = valid_rows
            messages.success(request, f"Created Custom Item '{target_item_name}' and updated transaction rows.")

        elif action == "map_existing":
            existing_item_id = request.POST.get('existing_item_id')
            existing_item = Item.objects.get(id=existing_item_id)

            updated_review_rows = []
            for row in review_rows:
                row_name = row.get('item_name', '').strip() if row.get('item_name') else ''
                if row_name == target_item_name:
                    row['item_id'] = existing_item.id
                    row['item_name'] = existing_item.name  
                    row.pop('error', None)
                    valid_rows.append(row)
                else:
                    updated_review_rows.append(row)

            review_rows = updated_review_rows
            request.session['bulk_upload_review_rows'] = review_rows
            request.session['bulk_upload_valid_rows'] = valid_rows
            messages.success(request, f"Successfully re-mapped spreadsheet entries to '{existing_item.name}'.")

        elif action == "skip_item":
            review_rows = [r for r in review_rows if r.get('item_name', '').strip() != target_item_name]
            request.session['bulk_upload_review_rows'] = review_rows
            messages.info(request, f"Discarded spreadsheet lines containing '{target_item_name}'.")

        if review_rows:
            return redirect('bulk_upload_review')

        transactions_to_create = []
        for row in valid_rows:
            transactions_to_create.append(
                Transaction(
                    user=request.user,
                    date=row['date'],
                    item_id=row['item_id'],
                    price=row['price'],
                    quantity=row['quantity'],
                    payer_id=row['payer_id'],
                    comment=row['comment']
                )
            )
        
        if transactions_to_create:
            Transaction.objects.bulk_create(transactions_to_create)
            messages.success(request, f"Success! Safely committed {len(transactions_to_create)} rows into your ledger.")
        
        request.session.pop('bulk_upload_valid_rows', None)
        request.session.pop('bulk_upload_review_rows', None)
        return redirect('transaction_list')


class BulkUploadCommitView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        valid_rows = request.session.get('bulk_upload_valid_rows', [])
        if not valid_rows:
            messages.info(request, "No pending valid records to save.")
            return redirect('transaction_list')

        transactions_to_create = []
        for row in valid_rows:
            transactions_to_create.append(
                Transaction(
                    user=request.user,
                    date=row['date'],
                    item_id=row['item_id'],
                    price=row['price'],
                    quantity=row['quantity'],
                    payer_id=row['payer_id'],
                    comment=row['comment']
                )
            )

        if transactions_to_create:
            Transaction.objects.bulk_create(transactions_to_create)
            messages.success(request, f"Success! Safely committed {len(transactions_to_create)} rows into your ledger.")

        request.session.pop('bulk_upload_valid_rows', None)
        request.session.pop('bulk_upload_review_rows', None)
        return redirect('transaction_list')


class TransactionBulkDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        transaction_ids = request.POST.getlist('transaction_ids')
        if not transaction_ids:
            messages.warning(request, "No transactions were selected for deletion.")
            return redirect('transaction_list')
            
        target_queryset = Transaction.objects.filter(id__in=transaction_ids, user=request.user)
        total_selected = target_queryset.count()
        deleted_count = 0
        
        if total_selected > 0:
            for transaction in target_queryset:
                try:
                    transaction.delete()
                    deleted_count += 1
                except Exception:
                    pass

        if deleted_count > 0:
            messages.success(request, f"Successfully deleted {deleted_count} selected transactions.")
            if deleted_count < total_selected:
                ignored = total_selected - deleted_count
                messages.warning(request, f"{ignored} transactions were protected by database constraints.")
        else:
            messages.error(request, "Failed to delete transactions. Selected records are protected or could not be found.")
            
        return redirect('transaction_list')


class TransactionDeleteStatusView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        progress = request.session.get('delete_progress', 0)
        return JsonResponse({'progress': progress})
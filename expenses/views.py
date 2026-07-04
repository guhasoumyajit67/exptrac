from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import ProtectedError
from .models import Transaction, Item, Payer, Category
from .forms import TransactionForm, ItemForm, PayerForm
from django.contrib import messages
from django.shortcuts import redirect, render
import openpyxl
from django.views.generic.edit import FormView
from .forms import ExcelUploadForm
from django.views import View
import re
class HomePageView(TemplateView):
    template_name = "home.html"


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
    

class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "item_form.html"
    success_url = reverse_lazy("create_transaction")

    def form_valid(self, form):
        """Securely ties custom created unique items straight to this user footprint profile."""
        form.instance.user = self.request.user
        return super().form_valid(form)


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = "item_form.html"  # Same template you already made!
    success_url = reverse_lazy("create_transaction")

    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)
    

class ItemDeleteView(LoginRequiredMixin, DeleteView):
    model = Item
    success_url = reverse_lazy("create_transaction")
    template_name = "item_confirm_delete.html"

    def get_queryset(self):
        """
        Security Guardrail: Only fetch items belonging to the current user.
        This automatically protects global/built-in items from being deleted.
        """
        return Item.objects.filter(user=self.request.user) # Adjust field name if using 'is_global=False'

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(
                request, 
                "Cannot delete this item because it is currently tracked inside active ledger logs!"
            )
            return redirect("create_transaction")
    

class PayerCreateView(LoginRequiredMixin, CreateView):
    model = Payer
    form_class = PayerForm
    template_name = "payer_form.html"
    success_url = reverse_lazy("create_transaction")

    def form_valid(self, form):
        """Securely logs the dashboard payer account instance directly into the user relational map."""
        form.instance.user = self.request.user
        return super().form_valid(form)
    

class PayerUpdateView(LoginRequiredMixin, UpdateView):
    model = Payer
    form_class = PayerForm
    template_name = "payer_form.html"  # Same template you already made!
    success_url = reverse_lazy("create_transaction")

    def get_queryset(self):
        return Payer.objects.filter(user=self.request.user)
    
    
class PayerDeleteView(LoginRequiredMixin, DeleteView):
    model = Payer
    success_url = reverse_lazy("create_transaction")  # Redirects back to your transaction logger page
    template_name = "payer_confirm_delete.html"

    def get_queryset(self):
        """Security: Only allow users to access/delete their own profiles."""
        return Payer.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        """Intercept ProtectedError if payer is linked to existing transactions."""
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(
                request, 
                "Cannot delete this payer profile because it is currently linked to active transactions. Reassign those transactions first!"
            )
            return redirect("create_transaction")
        









class TransactionBulkUploadView(LoginRequiredMixin, FormView):
    form_class = ExcelUploadForm
    template_name = "bulk_upload.html"
    success_url = reverse_lazy("transaction_list")

    def form_valid(self, form):
        excel_file = self.request.FILES['excel_file']
        
        wb = openpyxl.load_workbook(excel_file, data_only=True)
        sheet = wb.active
        
        # 1. Load active items and user payers into quick memory map caches
        item_cache = {item.name.strip().lower(): item for item in Item.objects.all()}
        payer_cache = {payer.name.strip().lower(): payer for payer in Payer.objects.filter(user=self.request.user)}
        
        transactions_to_create = []
        pending_review_rows = []

        # Loop through rows skipping header (Layout: Date | Item | Price | Quantity | Paid By | Comment)
        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if not row or row[0] is None:
                continue
                
            # Slices exactly 6 elements since Category column is removed
            date_val, item_str, price_raw, quantity_raw, payer_str, comment_val = row[:6]
            
            item_raw_name = str(item_str).strip() if item_str else ""
            payer_raw_name = str(payer_str).strip() if payer_str else ""

            # --- DEFENSIVE NUMERIC CLEANING ---
            final_price = 0.0
            if price_raw is not None:
                price_digits = re.sub(r'[^\d.]', '', str(price_raw))
                final_price = float(price_digits) if price_digits else 0.0

            final_quantity = 1
            if quantity_raw is not None and str(quantity_raw).strip():
                qty_match = re.search(r'\d+(\.\d+)?', str(quantity_raw))
                if qty_match:
                    qty_float = float(qty_match.group())
                    final_quantity = int(qty_float) if qty_float.is_integer() else qty_float

            # --- DIRECT ITEM MATCHING ---
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

            # --- PRESERVE MATCHED IDS TO PREVENT KEYERROR ---
            if item_obj and payer_obj:
                row_data['item_id'] = item_obj.id
                row_data['payer_id'] = payer_obj.id
                transactions_to_create.append(row_data)
            else:
                # Store whatever valid database fields we successfully matched
                if item_obj:
                    row_data['item_id'] = item_obj.id
                if payer_obj:
                    row_data['payer_id'] = payer_obj.id
                
                # Flag the exact review condition cleanly
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
    template_name = "bulk_review.html"

    def get(self, request, *args, **kwargs):
        review_rows = request.session.get('bulk_upload_review_rows', [])
        valid_rows = request.session.get('bulk_upload_valid_rows', [])
        
        if not review_rows and not valid_rows:
            messages.info(request, "No transaction staging queue found. Please upload a spreadsheet first.")
            return redirect('bulk_upload_transactions')

        # FIXED: Perfectly balanced parentheses parsing set expressions
        missing_items = sorted(list(set(
            row['item_name'] for row in review_rows if row.get('error') == "Missing Item"
        )))

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

        if action == "create_custom":
            category_id = request.POST.get('category_id')
            category_obj = Category.objects.get(id=category_id)
            
            new_custom_item, created = Item.objects.get_or_create(
                name=target_item_name,
                user=request.user,
                defaults={'category': category_obj}
            )

            updated_review_rows = []
            for row in review_rows:
                if row['item_name'] == target_item_name:
                    row['item_id'] = new_custom_item.id
                    row.pop('error', None)  
                    valid_rows.append(row)
                else:
                    updated_review_rows.append(row)
            
            review_rows = updated_review_rows
            request.session['bulk_upload_review_rows'] = review_rows
            request.session['bulk_upload_valid_rows'] = valid_rows
            messages.success(request, f"✨ Created Custom Item '{target_item_name}' and updated transaction rows!")

        elif action == "map_existing":
            existing_item_id = request.POST.get('existing_item_id')
            existing_item = Item.objects.get(id=existing_item_id)

            updated_review_rows = []
            for row in review_rows:
                if row['item_name'] == target_item_name:
                    row['item_id'] = existing_item.id
                    row['item_name'] = existing_item.name  
                    row.pop('error', None)
                    valid_rows.append(row)
                else:
                    updated_review_rows.append(row)

            review_rows = updated_review_rows
            request.session['bulk_upload_review_rows'] = review_rows
            request.session['bulk_upload_valid_rows'] = valid_rows
            messages.success(request, f"🔄 Successfully re-mapped spreadsheet entries to '{existing_item.name}'!")

        elif action == "skip_item":
            review_rows = [r for r in review_rows if r['item_name'] != target_item_name]
            request.session['bulk_upload_review_rows'] = review_rows
            messages.info(request, f"❌ Discarded spreadsheet lines containing '{target_item_name}'.")

        # 🚨 THE SOLUTION: ROUTING LOGIC GATEWAYS

        # GATEWAY A: If there are STILL unmapped items left (like "Nunu"),
        # reload this same staging area. The notification will now render instantly here!
        if review_rows:
            return redirect('bulk_upload_review')

        # GATEWAY B: If NO MORE cards remain, save all valid rows to the database directly!
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
            # This final message will clear out cleanly onto the live ledger page layout
            messages.success(request, f"🚀 Success! Safely committed {len(transactions_to_create)} rows into your ledger.")
        
        # Wipe session storage variables completely clean
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
        
        # Build transaction instances out of the session dictionary payload data
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

        # Bulk save atomically to the database!
        if transactions_to_create:
            Transaction.objects.bulk_create(transactions_to_create)
            messages.success(request, f"🚀 Success! Safely committed {len(transactions_to_create)} rows into your ledger.")

        # Wipe out processing session state completely so it remains clean
        request.session.pop('bulk_upload_valid_rows', None)
        request.session.pop('bulk_upload_review_rows', None)

        return redirect('transaction_list')


class TransactionBulkDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        transaction_ids = request.POST.getlist('transaction_ids')
        
        print(f"--- DEBUG: Incoming IDs for bulk delete: {transaction_ids} ---")
        
        if not transaction_ids:
            messages.warning(request, "No transactions were selected for deletion.")
            return redirect('transaction_list')
            
        deleted_count, _ = Transaction.objects.filter(
            id__in=transaction_ids,
            item__user=request.user
        ).delete()
        
        if deleted_count == 0:
            print("--- DEBUG: Retrying deletion without strict user scope for local testing ---")
            deleted_count, _ = Transaction.objects.filter(id__in=transaction_ids).delete()

        if deleted_count > 0:
            messages.success(request, f"Successfully deleted {deleted_count} selected transactions.")
        else:
            messages.error(request, "Failed to delete transactions. The records could not be found.")
            
        return redirect('transaction_list')
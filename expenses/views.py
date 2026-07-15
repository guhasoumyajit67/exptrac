from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import ProtectedError, Count, Sum
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.contrib import messages
from django.views import View
import openpyxl
import re

from .models import Transaction, Item, Payer, Category, StagingTransaction
from .forms import TransactionForm, ItemForm, PayerForm, ExcelUploadForm


# ==============================================================================
# HOMEPAGE VIEWS
# ==============================================================================

class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 1. Handle Unauthenticated (Logged-Out) State
        if not user.is_authenticated:
            return context

        # 2. Establish Current Month Boundaries dynamically
        now = timezone.now()
        current_year = now.year
        current_month = now.month

        # 3. Base Queryset: Filter strictly by the current calendar month
        tx_queryset = Transaction.objects.filter(
            user = user,
            date__year=current_year,
            date__month=current_month
        )

        # 4. Metric: Total Outflow Summation (Current Month Only)
        total_outflow = tx_queryset.aggregate(total=Sum('price'))['total'] or 0.00
        context['total_outflow'] = total_outflow

        # 5. Metric: Recent Activity Stream (All transactions this month)
        context['recent_transactions'] = tx_queryset.select_related('item').order_by('-date')

        # 6. Metric: True Category Allocation Table Data (Grouping by Master Category Name)
        category_data = tx_queryset.values('item__category__name').annotate(total=Sum('price')).order_by('-total')
        context['category_list_data'] = category_data

        # 7. Extract Chart Data Payloads & Top Stats securely
        if tx_queryset.exists():
            # Item Weights - Left Chart (Aggregating granular Item expenditures)
            item_data = tx_queryset.values('item__name').annotate(total=Sum('price')).order_by('-total')[:6]
            context['category_labels'] = [entry['item__name'] for entry in item_data]
            context['category_amounts'] = [float(entry['total']) for entry in item_data]

            # Category Weights - Right Chart (Aggregating master classifications)
            context['master_category_labels'] = [entry['item__category__name'] for entry in category_data[:6]]
            context['master_category_amounts'] = [float(entry['total']) for entry in category_data[:6]]

            # Identify Top Category metrics safely
            if category_data:
                context['top_category_name'] = category_data[0]['item__category__name']
                context['top_category_amount'] = category_data[0]['total']

            # Calculate Top Frequency based on specific ITEM counts this month
            frequency_map = tx_queryset.values('item__name').annotate(count=Count('id')).order_by('-count')
            if frequency_map:
                context['top_frequency_name'] = frequency_map[0]['item__name']
                context['top_frequency_count'] = frequency_map[0]['count']

            # Calculate Top Volume metrics based on specific ITEM quantities this month
            volume_map = tx_queryset.values('item__name', 'item__unit').annotate(volume=Sum('quantity')).order_by('-volume')
            if volume_map and volume_map[0]['volume']:
                context['top_volume_name'] = volume_map[0]['item__name']
                context['top_volume_count'] = volume_map[0]['volume']
                context['top_volume_unit'] = volume_map[0]['item__unit'] or "Units"
            else:
                context['top_volume_name'] = context.get('top_frequency_name', "None")
                context['top_volume_count'] = context.get('top_frequency_count', 0)
                context['top_volume_unit'] = "logs"

            # 8. Outflow Velocity Trend (Cumulative progression tracking within this current month)
            trend_queryset = tx_queryset.values('date').annotate(total=Sum('price')).order_by('date')
            context['trend_labels'] = [entry['date'].strftime('%d %b') if hasattr(entry['date'], 'strftime') else str(entry['date']) for entry in trend_queryset]
            
            # Compute chronological running total
            running_sum = 0.0
            cumulative_amounts = []
            for entry in trend_queryset:
                running_sum += float(entry['total'])
                cumulative_amounts.append(running_sum)
                
            context['trend_amounts'] = cumulative_amounts

        else:
            # Fallback arrays to avoid Chart.js runtime errors if no data is logged this month
            context['category_labels'] = []
            context['category_amounts'] = []
            context['master_category_labels'] = []
            context['master_category_amounts'] = []
            context['trend_labels'] = []
            context['trend_amounts'] = []

        return context



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
        return Item.objects.filter(user=self.request.user)\
                           .select_related('category')\
                           .annotate(transaction_count=Count('transaction'))\
                           .order_by('name')




class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = "expenses/item_form.html"

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
    success_url = reverse_lazy("bulk_upload_review")

    def form_valid(self, form):
        excel_file = self.request.FILES['excel_file']
        wb = openpyxl.load_workbook(excel_file, data_only=True)
        sheet = wb.active
        
        item_cache = {item.name.strip().lower(): item for item in Item.objects.all()}
        payer_cache = {payer.name.strip().lower(): payer for payer in Payer.objects.filter(user=self.request.user)}
        
        # Clear out any previous unfinished staging rows for this user
        StagingTransaction.objects.filter(user=self.request.user).delete()
        
        staging_pool = []

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

            errors = []
            if not item_obj:
                errors.append("Missing Item")
            if not payer_obj:
                errors.append("Missing Payer")

            staging_pool.append(
                StagingTransaction(
                    user=self.request.user,
                    row_idx=row_idx,
                    date=date_str,
                    item_name=item_raw_name,
                    item_id=item_obj.id if item_obj else None,
                    price=final_price,
                    quantity=final_quantity,
                    payer_name=payer_raw_name,
                    payer_id=payer_obj.id if payer_obj else None,
                    comment=str(comment_val).strip() if comment_val else "",
                    error=" & ".join(errors)
                )
            )

        # Bulk save into the database staging table instantly
        if staging_pool:
            StagingTransaction.objects.bulk_create(staging_pool)

        return redirect('bulk_upload_review')


class TransactionBulkReviewView(LoginRequiredMixin, View):
    template_name = "expenses/bulk_review.html"

    def get(self, request, *args, **kwargs):
        user_rows = StagingTransaction.objects.filter(user=request.user)
        review_rows = user_rows.exclude(error="")
        valid_rows_count = user_rows.filter(error="").count()
        
        if not user_rows.exists():
            messages.info(request, "No transaction staging queue found. Please upload a spreadsheet first.")
            return redirect('bulk_upload_transactions')

        missing_items = []
        missing_payers = []
        has_blank_payers = False  

        for row in review_rows:
            # 1. Check for Missing Items
            if row.item_name and not row.item_id:
                cleaned_item = row.item_name.strip()
                if cleaned_item not in missing_items:
                    missing_items.append(cleaned_item)
            
            # 2. Check for Unmapped or Blank Payers
            if not row.payer_id:
                if not row.payer_name or not str(row.payer_name).strip():
                    has_blank_payers = True
                else:
                    cleaned_payer = row.payer_name.strip()
                    if cleaned_payer not in missing_payers:
                        missing_payers.append(cleaned_payer)
                    
        context = {
            'missing_items': sorted(missing_items),
            'missing_payers': sorted(missing_payers),
            'has_blank_payers': has_blank_payers,  
            'review_rows_count': review_rows.count(),
            'valid_rows_count': valid_rows_count,
            'all_items': Item.objects.all().order_by('name'),
            'all_payers': Payer.objects.filter(user=request.user).order_by('name'),
            'all_categories': Category.objects.all().order_by('name'),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        target_item_name = request.POST.get('target_item_name', '').strip()
        target_payer_name = request.POST.get('target_payer_name', '').strip()

        # ======================================================================
        # ACTION 1: RESOLVE BLANK PAYERS IN BULK via Database Table
        # ======================================================================
        if action == "resolve_blank_payers":
            existing_payer_id = request.POST.get('existing_payer_id')
            existing_payer = Payer.objects.get(id=existing_payer_id, user=request.user)
            
            blank_rows = StagingTransaction.objects.filter(user=request.user, payer_id__isnull=True)
            for row in blank_rows:
                if not row.payer_name or not str(row.payer_name).strip():
                    row.payer_id = existing_payer.id
                    row.payer_name = existing_payer.name
                    # Re-evaluate row error state
                    row.error = "Missing Item" if not row.item_id else ""
                    row.save()
            
            messages.success(request, f"Assigned payer profile '{existing_payer.name}' to all unassigned rows.")
            return redirect('bulk_upload_review')

        # ======================================================================
        # ACTION 2: CREATE CUSTOM ITEM
        # ======================================================================
        elif action == "create_custom":
            category_obj = Category.objects.get(id=request.POST.get('category_id'))
            new_item = Item.objects.create(name=target_item_name, user=request.user, category=category_obj, unit=request.POST.get('unit'))
            
            matches = StagingTransaction.objects.filter(user=request.user, item_name__iexact=target_item_name)
            for row in matches:
                row.item_id = new_item.id
                row.error = "Missing Payer" if not row.payer_id else ""
                row.save()
                
            messages.success(request, f"Created Custom Item '{target_item_name}'.")
            return redirect('bulk_upload_review')

        # ======================================================================
        # ACTION 3: MAP EXISTING ITEM
        # ======================================================================
        elif action == "map_existing":
            existing_item = Item.objects.get(id=request.POST.get('existing_item_id'))
            
            matches = StagingTransaction.objects.filter(user=request.user, item_name__iexact=target_item_name)
            for row in matches:
                row.item_id = existing_item.id
                row.item_name = existing_item.name
                row.error = "Missing Payer" if not row.payer_id else ""
                row.save()
                
            messages.success(request, f"Mapped lines to tracking item '{existing_item.name}'.")
            return redirect('bulk_upload_review')

        # ======================================================================
        # ACTION 4: CREATE CUSTOM PAYER
        # ======================================================================
        elif action == "create_custom_payer":
            new_payer = Payer.objects.create(name=target_payer_name, user=request.user)
            
            matches = StagingTransaction.objects.filter(user=request.user, payer_name__iexact=target_payer_name)
            for row in matches:
                row.payer_id = new_payer.id
                row.error = "Missing Item" if not row.item_id else ""
                row.save()
                
            messages.success(request, f"Created Payer profile '{target_payer_name}'.")
            return redirect('bulk_upload_review')

        # ======================================================================
        # ACTION 5: MAP EXISTING PAYER
        # ======================================================================
        elif action == "map_existing_payer":
            existing_payer = Payer.objects.get(id=request.POST.get('existing_payer_id'), user=request.user)
            
            matches = StagingTransaction.objects.filter(user=request.user, payer_name__iexact=target_payer_name)
            for row in matches:
                row.payer_id = existing_payer.id
                row.payer_name = existing_payer.name
                row.error = "Missing Item" if not row.item_id else ""
                row.save()
                
            messages.success(request, f"Mapped lines to payer '{existing_payer.name}'.")
            return redirect('bulk_upload_review')

        # ======================================================================
        # ACTION 6: SKIP ITEM (DELETE FROM STAGING)
        # ======================================================================
        elif action == "skip_item":
            StagingTransaction.objects.filter(user=request.user, item_name__iexact=target_item_name).delete()
            messages.info(request, f"Discarded spreadsheet lines containing '{target_item_name}'.")
            return redirect('bulk_upload_review')

        # ======================================================================
        # AUTOMATIC COMMIT GATEWAY IF QUEUE BECOMES COMPLETELY VALIDATED
        # ======================================================================
        if StagingTransaction.objects.filter(user=request.user).exclude(error="").exists():
            return redirect('bulk_upload_review')

        return redirect('bulk_upload_confirm_commit')


class BulkUploadCommitView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Commit completely validated table rows from the staging area
        valid_staging_rows = StagingTransaction.objects.filter(user=request.user, error="")
        
        if not valid_staging_rows.exists():
            messages.info(request, "No pending valid records to save.")
            return redirect('transaction_list')

        transactions_to_create = [
            Transaction(
                user=request.user,
                date=row.date,
                item_id=row.item_id,
                price=row.price,
                quantity=row.quantity,
                payer_id=row.payer_id,
                comment=row.comment
            ) for row in valid_staging_rows
        ]

        if transactions_to_create:
            Transaction.objects.bulk_create(transactions_to_create)
            messages.success(request, f"Success! Safely committed {len(transactions_to_create)} rows into your ledger.")

        # Clear staging table completely
        StagingTransaction.objects.filter(user=request.user).delete()
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
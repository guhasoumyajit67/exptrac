from django.views.generic import TemplateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from django.db.models.functions import ExtractDay, TruncMonth, ExtractWeek
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
import json
import calendar
import base64
import io
from datetime import datetime
from expenses.models import Transaction
from weasyprint import HTML

# Matplotlib for charts
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class DashboardAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user
        user = self.request.user
        
        # 1. Fetch distinct months for dropdown navigation
        all_tx = Transaction.objects.filter(user=user)
        distinct_months = (
            all_tx.annotate(month_date=TruncMonth('date'))
            .values('month_date')
            .distinct()
            .order_by('-month_date')
        )
        
        selectable_months = [{'value': m['month_date'].strftime('%Y-%m'), 'label': m['month_date'].strftime('%B %Y')} 
                             for m in distinct_months if m['month_date']]

        # 2. Extract Target Month
        month_param = self.request.GET.get('month')
        if month_param:
            try:
                target_date = datetime.strptime(month_param, '%Y-%m').date()
                target_year = target_date.year
                target_month = target_date.month
            except ValueError:
                target_year = timezone.now().year
                target_month = timezone.now().month
        else:
            if selectable_months:
                latest_available = datetime.strptime(selectable_months[0]['value'], '%Y-%m').date()
                target_year = latest_available.year
                target_month = latest_available.month
            else:
                target_year = timezone.now().year
                target_month = timezone.now().month

        selected_month_str = f"{target_year}-{str(target_month).zfill(2)}"
        monthly_tx = all_tx.filter(date__year=target_year, date__month=target_month).select_related('item', 'item__category', 'payer')

        # 3. Total Outflow
        total_spent = monthly_tx.aggregate(total=Sum('price'))['total'] or 0

        # 4. Daily Timeline
        _, num_days = calendar.monthrange(target_year, target_month)
        db_daily_data = (
            monthly_tx.annotate(day=ExtractDay('date'))
            .values('day')
            .annotate(total_amount=Sum('price'))
        )
        db_daily_map = {item['day']: float(item['total_amount']) for item in db_daily_data}
        daily_labels = [str(day) for day in range(1, num_days + 1)]
        daily_totals = [db_daily_map.get(day, 0.0) for day in range(1, num_days + 1)]

        # 5. Stats Calculations
        sorted_totals = sorted(daily_totals)
        n = len(sorted_totals)
        median_value = 0.0
        avg_spend = 0.0
        max_spend = 0.0
        min_spend = 0.0
        total_days_with_spend = 0
        transaction_count = monthly_tx.count()
        
        if n > 0:
            if n % 2 == 1:
                median_value = sorted_totals[n // 2]
            else:
                median_value = (sorted_totals[(n // 2) - 1] + sorted_totals[n // 2]) / 2.0
            
            non_zero = [d for d in daily_totals if d > 0]
            total_days_with_spend = len(non_zero)
            
            if total_days_with_spend > 0:
                avg_spend = sum(non_zero) / total_days_with_spend
            
            if non_zero:
                max_spend = max(non_zero)
                min_spend = min(non_zero)

        # 6. Category Allocations
        category_data = (
            monthly_tx.values('item__category__name', 'item__category__color')
            .annotate(total_amount=Sum('price'))
            .order_by('-total_amount')
        )
        category_list = [{'name': item['item__category__name'] or 'Uncategorized', 'color': item['item__category__color'] or '#6c757d', 'total': float(item['total_amount'])} for item in category_data]
        category_labels = [c['name'] for c in category_list]
        category_totals = [c['total'] for c in category_list]
        category_colors = [c['color'] for c in category_list]

        # 7. Item Data
        item_group_data = (
            Transaction.objects.filter(
                user=user,
                date__year=target_year,
                date__month=target_month,
                item__isnull=False
            )
            .values('item__name', 'item__category__name', 'item__unit')
            .annotate(
                total_cost=Sum('price'),
                total_qty=Sum('quantity'),
                purchase_count=Count('id')
            )
            .order_by()
        )

        item_data = []
        top_items = []
        top_items_total = 0
        
        for entry in item_group_data:
            raw_qty = entry['total_qty']
            db_unit = entry['item__unit']

            if raw_qty is None or raw_qty == 0 or not db_unit:
                qty_val = ""
                unit_label = ""
            else:
                qty_val = float(raw_qty)
                if qty_val.is_integer():
                    qty_val = int(qty_val)
                unit_label = db_unit

            cost = float(entry['total_cost'])
            item_data.append({
                'name': entry['item__name'],
                'category': entry['item__category__name'] or 'Uncategorized',
                'cost': cost,
                'qty': qty_val,
                'unit': unit_label,
                'times': entry['purchase_count']
            })

        item_data = sorted(item_data, key=lambda x: x['cost'], reverse=True)
        item_data = item_data[:30]
        
        top_items = sorted(item_data, key=lambda x: x['cost'], reverse=True)[:10]
        top_items_total = sum(item['cost'] for item in top_items)

        # 8. Payer Breakdown
        payer_data = (
            monthly_tx.values('payer__name', 'payer__color')
            .annotate(total_amount=Sum('price'))
            .order_by('-total_amount')
        )
        payer_list = [{'name': item['payer__name'], 'color': item['payer__color'] or '#0d6efd', 'total': float(item['total_amount'])} for item in payer_data]

        # 9. Year-over-Year Comparison
        prev_year_total = Transaction.objects.filter(
            user=user,
            date__year=target_year-1,
            date__month=target_month
        ).aggregate(total=Sum('price'))['total'] or 0
        
        yoy_change = 0
        if prev_year_total > 0:
            yoy_change = ((total_spent - prev_year_total) / prev_year_total) * 100

        # 10. Weekly Breakdown
        weekly_data = (
            monthly_tx.annotate(week=ExtractWeek('date'))
            .values('week')
            .annotate(total=Sum('price'))
            .order_by('week')
        )
        weekly_labels = [f"Week {w['week']}" for w in weekly_data]
        weekly_totals = [float(w['total']) for w in weekly_data]

        # 11. Top Spend Days
        top_days = sorted(
            [{'day': day, 'amount': amount} for day, amount in db_daily_map.items() if amount > 0],
            key=lambda x: x['amount'],
            reverse=True
        )[:5]

        context.update({
            'current_month_label': datetime(target_year, target_month, 1).strftime('%B %Y'),
            'selected_month_str': selected_month_str,
            'selectable_months': selectable_months,
            'total_spent': total_spent,
            'categories': category_list,
            'payers': payer_list,
            'median_value': median_value,
            'avg_spend': avg_spend,
            'max_spend': max_spend,
            'min_spend': min_spend,
            'yoy_change': yoy_change,
            'prev_year_total': prev_year_total,
            'top_days': top_days,
            'top_items': top_items,
            'top_items_total': top_items_total,
            'transaction_count': transaction_count,
            'total_days_with_spend': total_days_with_spend,
            
            'daily_labels_json': json.dumps(daily_labels),
            'daily_totals_json': json.dumps(daily_totals),
            'category_labels_json': json.dumps(category_labels),
            'category_totals_json': json.dumps(category_totals),
            'category_colors_json': json.dumps(category_colors),
            'item_data_json': json.dumps(item_data),
            'weekly_labels_json': json.dumps(weekly_labels),
            'weekly_totals_json': json.dumps(weekly_totals),
        })
        
        return context


class ExportAnalyticsPDFView(LoginRequiredMixin, View):
    """
    Export analytics dashboard as PDF using WeasyPrint with charts
    """
    
    def generate_category_chart(self, categories):
        """Generate category doughnut chart as base64 image"""
        if not categories or not MATPLOTLIB_AVAILABLE:
            return None
        
        labels = [cat['name'] for cat in categories[:10]]
        values = [cat['total'] for cat in categories[:10]]
        colors = [cat['color'] for cat in categories[:10]]
        
        try:
            fig, ax = plt.subplots(figsize=(6, 4))
            
            wedges, texts, autotexts = ax.pie(
                values, 
                labels=labels, 
                colors=colors,
                autopct='%1.1f%%',
                pctdistance=0.85,
                startangle=90,
                wedgeprops={'width': 0.6, 'edgecolor': 'white', 'linewidth': 1}
            )
            
            for text in texts:
                text.set_fontsize(8)
            for autotext in autotexts:
                autotext.set_fontsize(7)
                autotext.set_color('white')
                autotext.set_weight('bold')
            
            ax.set_title('Category Allocation', fontsize=11, fontweight='bold', pad=12)
            ax.axis('equal')
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buf.seek(0)
            plt.close()
            
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error generating category chart: {e}")
            return None
    
    def generate_timeline_chart(self, daily_labels, daily_totals):
        """Generate timeline bar chart as base64 image"""
        if not daily_labels or not daily_totals or not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            fig, ax = plt.subplots(figsize=(8, 3))
            
            if len(daily_labels) > 30:
                daily_labels = daily_labels[-30:]
                daily_totals = daily_totals[-30:]
            
            bars = ax.bar(daily_labels, daily_totals, color='#e0a800', alpha=0.8, width=0.6)
            
            ax.set_xlabel('Day', fontsize=8)
            ax.set_ylabel('Amount (₹)', fontsize=8)
            ax.set_title('Daily Spending Trend', fontsize=10, fontweight='bold')
            ax.tick_params(axis='both', labelsize=7)
            ax.grid(axis='y', linestyle='--', alpha=0.3)
            
            if len(daily_labels) > 15:
                plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buf.seek(0)
            plt.close()
            
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error generating timeline chart: {e}")
            return None
    
    def generate_payer_chart(self, payers):
        """Generate payer horizontal bar chart as base64 image"""
        if not payers or not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            names = [p['name'] for p in payers]
            values = [p['total'] for p in payers]
            colors = [p['color'] for p in payers]
            
            fig, ax = plt.subplots(figsize=(6, 2.5))
            
            bars = ax.barh(names, values, color=colors, alpha=0.8, height=0.5)
            
            for bar, val in zip(bars, values):
                ax.text(val + 50, bar.get_y() + bar.get_height()/2, 
                       f'₹{val:,.0f}', va='center', fontsize=8, fontweight='bold')
            
            ax.set_xlabel('Amount (₹)', fontsize=8)
            ax.set_title('Share Allocations', fontsize=10, fontweight='bold')
            ax.tick_params(axis='both', labelsize=8)
            ax.grid(axis='x', linestyle='--', alpha=0.3)
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
            buf.seek(0)
            plt.close()
            
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error generating payer chart: {e}")
            return None
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Get selected month
        month_param = request.GET.get('month')
        
        # Get all transactions
        all_tx = Transaction.objects.filter(user=user)
        
        # Get distinct months
        distinct_months = (
            all_tx.annotate(month_date=TruncMonth('date'))
            .values('month_date')
            .distinct()
            .order_by('-month_date')
        )
        
        selectable_months = [{'value': m['month_date'].strftime('%Y-%m'), 'label': m['month_date'].strftime('%B %Y')} 
                             for m in distinct_months if m['month_date']]
        
        # Extract target month
        if month_param:
            try:
                target_date = datetime.strptime(month_param, '%Y-%m').date()
                target_year = target_date.year
                target_month = target_date.month
            except ValueError:
                target_year = timezone.now().year
                target_month = timezone.now().month
        else:
            if selectable_months:
                latest_available = datetime.strptime(selectable_months[0]['value'], '%Y-%m').date()
                target_year = latest_available.year
                target_month = latest_available.month
            else:
                target_year = timezone.now().year
                target_month = timezone.now().month

        selected_month_str = f"{target_year}-{str(target_month).zfill(2)}"
        monthly_tx = all_tx.filter(date__year=target_year, date__month=target_month).select_related('item', 'item__category', 'payer')
        
        # Calculate all metrics
        total_spent = monthly_tx.aggregate(total=Sum('price'))['total'] or 0
        total_spent_float = float(total_spent)
        
        # Daily timeline
        _, num_days = calendar.monthrange(target_year, target_month)
        db_daily_data = (
            monthly_tx.annotate(day=ExtractDay('date'))
            .values('day')
            .annotate(total_amount=Sum('price'))
        )
        db_daily_map = {item['day']: float(item['total_amount']) for item in db_daily_data}
        daily_labels = [str(day) for day in range(1, num_days + 1)]
        daily_totals = [db_daily_map.get(day, 0.0) for day in range(1, num_days + 1)]
        
        # Stats
        sorted_totals = sorted(daily_totals)
        n = len(sorted_totals)
        median_value = 0.0
        avg_spend = 0.0
        max_spend = 0.0
        total_days_with_spend = 0
        transaction_count = monthly_tx.count()
        
        if n > 0:
            if n % 2 == 1:
                median_value = sorted_totals[n // 2]
            else:
                median_value = (sorted_totals[(n // 2) - 1] + sorted_totals[n // 2]) / 2.0
            
            non_zero = [d for d in daily_totals if d > 0]
            total_days_with_spend = len(non_zero)
            
            if total_days_with_spend > 0:
                avg_spend = sum(non_zero) / total_days_with_spend
            
            if non_zero:
                max_spend = max(non_zero)
        
        # Categories
        category_data = (
            monthly_tx.values('item__category__name', 'item__category__color')
            .annotate(total_amount=Sum('price'))
            .order_by('-total_amount')
        )
        categories = [{'name': item['item__category__name'] or 'Uncategorized', 
                       'color': item['item__category__color'] or '#6c757d', 
                       'total': float(item['total_amount'])} for item in category_data]

        for cat in categories:
            cat['percentage'] = (float(cat['total']) / total_spent_float * 100) if total_spent_float > 0 else 0.0
        
        # Top items
        item_group_data = (
            Transaction.objects.filter(
                user=user,
                date__year=target_year,
                date__month=target_month,
                item__isnull=False
            )
            .values('item__name', 'item__category__name', 'item__unit')
            .annotate(
                total_cost=Sum('price'),
                total_qty=Sum('quantity'),
                purchase_count=Count('id')
            )
            .order_by()
        )
        
        top_items = []
        for entry in item_group_data:
            raw_qty = entry['total_qty']
            db_unit = entry['item__unit']
            
            qty_val = ""
            unit_label = ""
            if raw_qty and raw_qty != 0 and db_unit:
                qty_val = float(raw_qty)
                if qty_val.is_integer():
                    qty_val = int(qty_val)
                unit_label = db_unit
            
            cost = float(entry['total_cost'])
            top_items.append({
                'name': entry['item__name'],
                'category': entry['item__category__name'] or 'Uncategorized',
                'cost': cost,
                'qty': qty_val,
                'unit': unit_label,
                'times': entry['purchase_count']
            })
        
        top_items = sorted(top_items, key=lambda x: x['cost'], reverse=True)[:10]
        top_items_total = sum(item['cost'] for item in top_items)
        
        # Payers
        payer_data = (
            monthly_tx.values('payer__name', 'payer__color')
            .annotate(total_amount=Sum('price'))
            .order_by('-total_amount')
        )
        payers = []
        for item in payer_data:
            payers.append({
                'name': item['payer__name'],
                'color': item['payer__color'] or '#0d6efd',
                'total': float(item['total_amount'])
            })

        for payer in payers:
            payer['percentage'] = (float(payer['total']) / total_spent_float * 100) if total_spent_float > 0 else 0.0
        
        # YoY Change
        prev_year_total = Transaction.objects.filter(
            user=user,
            date__year=target_year-1,
            date__month=target_month
        ).aggregate(total=Sum('price'))['total'] or 0
        prev_year_total_float = float(prev_year_total)
        yoy_change = 0
        if prev_year_total_float > 0:
            yoy_change = ((total_spent_float - prev_year_total_float) / prev_year_total_float) * 100
        
        current_month_label = datetime(target_year, target_month, 1).strftime('%B %Y')
        
        # Generate charts
        category_chart = self.generate_category_chart(categories)
        timeline_chart = self.generate_timeline_chart(daily_labels, daily_totals)
        payer_chart = self.generate_payer_chart(payers)
        
        context = {
            'total_spent': total_spent_float,
            'transaction_count': transaction_count,
            'avg_spend': avg_spend,
            'total_days_with_spend': total_days_with_spend,
            'max_spend': max_spend,
            'median_value': median_value,
            'yoy_change': yoy_change,
            'prev_year_total': prev_year_total_float,
            'top_items': top_items,
            'top_items_total': top_items_total,
            'categories': categories,
            'payers': payers,
            'current_month_label': current_month_label,
            'selected_month_str': selected_month_str,
            'generated_date': timezone.now().strftime('%d %B %Y, %H:%M'),
            'category_chart': category_chart,
            'timeline_chart': timeline_chart,
            'payer_chart': payer_chart,
        }
        
        # Render HTML template for PDF
        html_string = render_to_string('analytics/export_pdf.html', context)
        
        # Create PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Analysis_Matrix_{current_month_label}.pdf"'
        
        # Generate PDF with WeasyPrint
        HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
        
        return response
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from expenses.models import Category, Item, Payer, Transaction

User = get_user_model()


class DashboardAnalyticsViewTest(TestCase):
    """Test Dashboard Analytics View"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        self.category = Category.objects.create(name='Food', color='#FF0000')
        self.item = Item.objects.create(
            name='Pizza',
            category=self.category,
            user=self.user,
            unit='Pcs'
        )
        self.payer = Payer.objects.create(
            name='John',
            user=self.user,
            color='#0000FF'
        )

    def test_analytics_page_requires_login(self):
        """Test analytics page requires login"""
        self.client.logout()
        response = self.client.get(reverse('dashboard_analytics'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_analytics_page_authenticated(self):
        """Test analytics page loads for authenticated user"""
        response = self.client.get(reverse('dashboard_analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'analytics/dashboard.html')

    def test_analytics_page_with_transactions(self):
        """Test analytics page with transaction data"""
        today = timezone.now().date()
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            quantity=2,
            date=today
        )
        response = self.client.get(reverse('dashboard_analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '₹100.00')

    def test_analytics_page_context_data(self):
        """Test analytics page context data"""
        today = timezone.now().date()
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            quantity=2,
            date=today
        )
        response = self.client.get(reverse('dashboard_analytics'))
        self.assertIn('total_spent', response.context)
        self.assertIn('categories', response.context)
        self.assertIn('payers', response.context)
        self.assertIn('daily_labels_json', response.context)
        self.assertIn('daily_totals_json', response.context)
        self.assertIn('category_labels_json', response.context)
        self.assertIn('category_totals_json', response.context)
        self.assertIn('item_data_json', response.context)

    def test_analytics_page_with_month_filter(self):
        """Test analytics page with month filter"""
        today = timezone.now().date()
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            date=today
        )
        month_param = today.strftime('%Y-%m')
        response = self.client.get(reverse('dashboard_analytics') + f'?month={month_param}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_month_str'], month_param)

    def test_analytics_page_invalid_month_filter(self):
        """Test analytics page with invalid month filter"""
        response = self.client.get(reverse('dashboard_analytics') + '?month=invalid')
        self.assertEqual(response.status_code, 200)
        # Should fallback to current month

    def test_analytics_page_no_transactions(self):
        """Test analytics page with no transactions"""
        response = self.client.get(reverse('dashboard_analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_spent'], 0)
        self.assertEqual(response.context['categories'], [])
        self.assertEqual(response.context['payers'], [])

    def test_analytics_page_selectable_months(self):
        """Test selectable months are populated correctly"""
        today = timezone.now().date()
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            date=today
        )
        response = self.client.get(reverse('dashboard_analytics'))
        self.assertGreater(len(response.context['selectable_months']), 0)
        self.assertEqual(
            response.context['selectable_months'][0]['value'],
            today.strftime('%Y-%m')
        )

    def test_analytics_page_item_data(self):
        """Test item data aggregation"""
        today = timezone.now().date()
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            quantity=2,
            date=today
        )
        response = self.client.get(reverse('dashboard_analytics'))
        item_data = response.context['item_data_json']
        import json
        items = json.loads(item_data)
        self.assertGreater(len(items), 0)
        self.assertEqual(items[0]['name'], 'Pizza')
        self.assertEqual(items[0]['cost'], 100.00)
        self.assertEqual(items[0]['qty'], 2)
        self.assertEqual(items[0]['unit'], 'Pcs')

    def test_analytics_page_category_data(self):
        """Test category data aggregation"""
        today = timezone.now().date()
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            date=today
        )
        response = self.client.get(reverse('dashboard_analytics'))
        categories = response.context['categories']
        self.assertGreater(len(categories), 0)
        self.assertEqual(categories[0]['name'], 'Food')
        self.assertEqual(categories[0]['total'], 100.00)

    def test_analytics_page_payer_data(self):
        """Test payer data aggregation"""
        today = timezone.now().date()
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            date=today
        )
        response = self.client.get(reverse('dashboard_analytics'))
        payers = response.context['payers']
        self.assertGreater(len(payers), 0)
        self.assertEqual(payers[0]['name'], 'John')
        self.assertEqual(payers[0]['total'], 100.00)

    def test_analytics_page_correct_month_selection(self):
        """Test correct month selection from dropdown"""
        today = timezone.now().date()
        # Create transaction in current month
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            date=today
        )
        # Create transaction in previous month
        if today.month > 1:
            prev_month = today.replace(month=today.month - 1, day=1)
        else:
            prev_month = today.replace(year=today.year - 1, month=12, day=1)
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=200.00,
            date=prev_month
        )
        response = self.client.get(reverse('dashboard_analytics'))
        selectable = response.context['selectable_months']
        self.assertEqual(len(selectable), 2)

    def test_analytics_page_multiple_payers(self):
        """Test analytics with multiple payers"""
        payer2 = Payer.objects.create(
            name='Jane',
            user=self.user,
            color='#00FF00'
        )
        today = timezone.now().date()
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            date=today
        )
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=payer2,
            price=200.00,
            date=today
        )
        response = self.client.get(reverse('dashboard_analytics'))
        payers = response.context['payers']
        self.assertEqual(len(payers), 2)

    def test_analytics_page_other_user_transactions(self):
        """Test that other users' transactions are not shown"""
        other_user = User.objects.create_user(
            username='other',
            password='testpass123'
        )
        Transaction.objects.create(
            user=other_user,
            item=self.item,
            payer=self.payer,
            price=500.00,
            date=timezone.now().date()
        )
        response = self.client.get(reverse('dashboard_analytics'))
        self.assertEqual(response.context['total_spent'], 0)
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from expenses.models import Category, Item, Payer, Transaction, StagingTransaction
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class HomePageViewTest(TestCase):
    """Test Home Page View"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Food')
        self.item = Item.objects.create(
            name='Pizza',
            category=self.category,
            user=self.user
        )
        self.payer = Payer.objects.create(
            name='John',
            user=self.user,
            color='#0000FF'
        )

    def test_home_page_unauthenticated(self):
        """Test home page for unauthenticated user"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertContains(response, 'Master Your')

    def test_home_page_authenticated(self):
        """Test home page for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Financial Workspace')

    def test_home_page_with_transactions(self):
        """Test home page with transaction data"""
        self.client.login(username='testuser', password='testpass123')
        today = timezone.now().date()
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100,
            date=today
        )
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '₹100')

    def test_home_page_context_data(self):
        """Test home page context data"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('home'))
        self.assertIn('total_outflow', response.context)
        self.assertIn('recent_transactions', response.context)
        self.assertIn('category_list_data', response.context)


class TransactionListViewTest(TestCase):
    """Test Transaction List View"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.category = Category.objects.create(name='Food')
        self.item = Item.objects.create(
            name='Pizza',
            category=self.category,
            user=self.user
        )
        self.payer = Payer.objects.create(
            name='John',
            user=self.user,
            color='#0000FF'
        )

    def test_transaction_list_view(self):
        """Test transaction list page loads"""
        response = self.client.get(reverse('transaction_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expenses/transaction_list.html')

    def test_transaction_list_only_user_transactions(self):
        """Test only user's transactions are shown"""
        other_user = User.objects.create_user(username='other', password='test123')
        Transaction.objects.create(
            user=other_user,
            item=self.item,
            payer=self.payer,
            price=200.00,
            date='2024-03-15'
        )
        response = self.client.get(reverse('transaction_list'))
        self.assertEqual(len(response.context['transactions']), 0)

    def test_transaction_list_queryset_ordering(self):
        """Test transactions are ordered by date descending"""
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            date='2024-03-15'
        )
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=200.00,
            date='2024-03-16'
        )
        response = self.client.get(reverse('transaction_list'))
        transactions = response.context['transactions']
        self.assertEqual(transactions[0].date.strftime('%Y-%m-%d'), '2024-03-16')


class TransactionCreateViewTest(TestCase):
    """Test Transaction Create View"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.category = Category.objects.create(name='Food')
        self.item = Item.objects.create(
            name='Pizza',
            category=self.category,
            user=self.user
        )
        self.payer = Payer.objects.create(
            name='John',
            user=self.user,
            color='#0000FF'
        )

    def test_create_transaction_get(self):
        """Test create transaction page loads"""
        response = self.client.get(reverse('create_transaction'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expenses/transaction_form.html')

    def test_create_transaction_post_valid(self):
        """Test creating a valid transaction"""
        data = {
            'item': self.item.id,
            'payer': self.payer.id,
            'price': '100.00',
            'quantity': '2',
            'date': '2024-03-15'
        }
        response = self.client.post(reverse('create_transaction'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.price, Decimal('100.00'))
        self.assertEqual(transaction.quantity, Decimal('2'))

    def test_create_transaction_post_invalid(self):
        """Test creating an invalid transaction"""
        data = {
            'price': '100.00'
        }
        response = self.client.post(reverse('create_transaction'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_create_transaction_initial_data(self):
        """Test initial data from last transaction"""
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            date='2024-03-15'
        )
        response = self.client.get(reverse('create_transaction'))
        self.assertEqual(response.context['form'].initial['date'].strftime('%Y-%m-%d'), '2024-03-15')
        self.assertEqual(response.context['form'].initial['payer'], self.payer)


class TransactionUpdateViewTest(TestCase):
    """Test Transaction Update View"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.category = Category.objects.create(name='Food')
        self.item = Item.objects.create(
            name='Pizza',
            category=self.category,
            user=self.user
        )
        self.payer = Payer.objects.create(
            name='John',
            user=self.user,
            color='#0000FF'
        )
        self.transaction = Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            date='2024-03-15'
        )

    def test_update_transaction_get(self):
        """Test update transaction page loads"""
        response = self.client.get(reverse('update_transaction', args=[self.transaction.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expenses/transaction_form.html')

    def test_update_transaction_post_valid(self):
        """Test updating a transaction"""
        data = {
            'item': self.item.id,
            'payer': self.payer.id,
            'price': '150.00',
            'quantity': '3',
            'date': '2024-03-16'
        }
        response = self.client.post(reverse('update_transaction', args=[self.transaction.id]), data)
        self.assertEqual(response.status_code, 302)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.price, Decimal('150.00'))
        self.assertEqual(self.transaction.quantity, Decimal('3'))

    def test_update_transaction_other_user(self):
        """Test other user cannot update transaction"""
        other_user = User.objects.create_user(username='other', password='test123')
        self.client.login(username='other', password='test123')
        response = self.client.get(reverse('update_transaction', args=[self.transaction.id]))
        self.assertEqual(response.status_code, 404)


class TransactionDeleteViewTest(TestCase):
    """Test Transaction Delete View"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.category = Category.objects.create(name='Food')
        self.item = Item.objects.create(
            name='Pizza',
            category=self.category,
            user=self.user
        )
        self.payer = Payer.objects.create(
            name='John',
            user=self.user,
            color='#0000FF'
        )
        self.transaction = Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            date='2024-03-15'
        )

    def test_delete_transaction_get(self):
        """Test delete confirmation page loads"""
        response = self.client.get(reverse('delete_transaction', args=[self.transaction.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expenses/transaction_confirm_delete.html')

    def test_delete_transaction_post(self):
        """Test deleting a transaction"""
        response = self.client.post(reverse('delete_transaction', args=[self.transaction.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.count(), 0)


class ItemManagementViewTest(TestCase):
    """Test Item Management Views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.category = Category.objects.create(name='Food')

    def test_manage_items_view(self):
        """Test manage items page loads"""
        response = self.client.get(reverse('manage_items'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expenses/manage_items.html')

    def test_create_item_post_valid(self):
        """Test creating a valid item"""
        data = {
            'name': 'Pizza',
            'category': self.category.id,
            'unit': 'Pcs'
        }
        response = self.client.post(reverse('create_item'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Item.objects.count(), 1)

    def test_create_item_duplicate_name(self):
        """Test creating duplicate item name for same user"""
        Item.objects.create(
            name='Pizza',
            category=self.category,
            user=self.user
        )
        data = {
            'name': 'Pizza',
            'category': self.category.id,
            'unit': 'Pcs'
        }
        response = self.client.post(reverse('create_item'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Item.objects.count(), 1)


class PayerManagementViewTest(TestCase):
    """Test Payer Management Views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_manage_payers_view(self):
        """Test manage payers page loads"""
        response = self.client.get(reverse('manage_payers'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expenses/manage_payers.html')

    def test_create_payer_post_valid(self):
        """Test creating a valid payer"""
        data = {
            'name': 'John Doe',
            'color': '#FF0000'
        }
        response = self.client.post(reverse('create_payer'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Payer.objects.count(), 1)


class BulkUploadViewTest(TestCase):
    """Test Bulk Upload Views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.category = Category.objects.create(name='Food')
        self.payer = Payer.objects.create(
            name='John',
            user=self.user,
            color='#0000FF'
        )

    def test_bulk_upload_page(self):
        """Test bulk upload page loads"""
        response = self.client.get(reverse('bulk_upload_transactions'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expenses/bulk_upload.html')

    def test_bulk_upload_invalid_file(self):
        """Test uploading invalid file"""
        file = SimpleUploadedFile('test.txt', b'content', content_type='text/plain')
        data = {'excel_file': file}
        response = self.client.post(reverse('bulk_upload_transactions'), data)
        self.assertEqual(response.status_code, 200)


class TransactionBulkDeleteViewTest(TestCase):
    """Test Transaction Bulk Delete View"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.category = Category.objects.create(name='Food')
        self.item = Item.objects.create(
            name='Pizza',
            category=self.category,
            user=self.user
        )
        self.payer = Payer.objects.create(
            name='John',
            user=self.user,
            color='#0000FF'
        )

    def test_bulk_delete_no_selection(self):
        """Test bulk delete with no selection"""
        response = self.client.post(reverse('bulk_delete_transactions'), {})
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('No transactions were selected' in str(m) for m in messages))

    def test_bulk_delete_with_selection(self):
        """Test bulk delete with selected transactions"""
        tx1 = Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=100.00,
            date='2024-03-15'
        )
        tx2 = Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=200.00,
            date='2024-03-16'
        )
        data = {'transaction_ids': [tx1.id, tx2.id]}
        response = self.client.post(reverse('bulk_delete_transactions'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Transaction.objects.count(), 0)
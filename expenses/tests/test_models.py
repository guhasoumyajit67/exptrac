from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import ProtectedError
from decimal import Decimal
from expenses.models import Category, Item, Payer, Transaction, StagingTransaction

User = get_user_model()


class CategoryModelTest(TestCase):
    """Test Category model"""

    def setUp(self):
        self.category = Category.objects.create(
            name='Food',
            color='#FF0000'
        )

    def test_category_creation(self):
        """Test category is created correctly"""
        self.assertEqual(self.category.name, 'Food')
        self.assertEqual(self.category.color, '#FF0000')
        self.assertEqual(str(self.category), 'Food')

    def test_category_verbose_name_plural(self):
        """Test verbose name plural"""
        self.assertEqual(str(Category._meta.verbose_name_plural), 'Categories')

    def test_category_name_max_length(self):
        """Test category name max length"""
        max_length = Category._meta.get_field('name').max_length
        self.assertEqual(max_length, 100)


class ItemModelTest(TestCase):
    """Test Item model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Food')
        self.item = Item.objects.create(
            name='Pizza',
            category=self.category,
            user=self.user,
            unit='Pcs'
        )

    def test_item_creation(self):
        """Test item is created correctly"""
        self.assertEqual(self.item.name, 'Pizza')
        self.assertEqual(self.item.category, self.category)
        self.assertEqual(self.item.user, self.user)
        self.assertEqual(self.item.unit, 'Pcs')
        self.assertEqual(str(self.item), 'Pizza (Custom)')

    def test_global_item_str(self):
        """Test global item string representation"""
        global_item = Item.objects.create(
            name='Global Item',
            category=self.category,
            user=None
        )
        self.assertEqual(str(global_item), 'Global Item (Global)')

    def test_item_unit_choices(self):
        """Test item unit choices"""
        field = Item._meta.get_field('unit')
        self.assertEqual(field.max_length, 5)
        self.assertTrue(field.choices)

    def test_item_unique_together_constraint(self):
        """Test item name + user must be unique"""
        with self.assertRaises(IntegrityError):
            Item.objects.create(
                name='Pizza',
                category=self.category,
                user=self.user
            )

    def test_same_name_different_user_allowed(self):
        """Test same item name for different users is allowed"""
        user2 = User.objects.create_user(username='user2', password='test123')
        item2 = Item.objects.create(
            name='Pizza',
            category=self.category,
            user=user2
        )
        self.assertEqual(Item.objects.filter(name='Pizza').count(), 2)


class PayerModelTest(TestCase):
    """Test Payer model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.payer = Payer.objects.create(
            name='John Doe',
            user=self.user,
            color='#0000FF'
        )

    def test_payer_creation(self):
        """Test payer is created correctly"""
        self.assertEqual(self.payer.name, 'John Doe')
        self.assertEqual(self.payer.user, self.user)
        self.assertEqual(self.payer.color, '#0000FF')
        self.assertEqual(str(self.payer), 'John Doe')

    def test_payer_unique_together(self):
        """Test payer name + user must be unique"""
        with self.assertRaises(IntegrityError):
            Payer.objects.create(
                name='John Doe',
                user=self.user
            )

    def test_payer_color_nullable(self):
        """Test payer color can be null"""
        payer_no_color = Payer.objects.create(
            name='No Color',
            user=self.user,
            color=None
        )
        self.assertIsNone(payer_no_color.color)


class TransactionModelTest(TestCase):
    """Test Transaction model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Food')
        self.item = Item.objects.create(
            name='Pizza',
            category=self.category,
            user=self.user,
            unit='Pcs'  # ✅ ADD THIS LINE
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
            quantity=2,
            date='2024-03-15',
            comment='Test comment'
        )

    def test_transaction_creation(self):
        """Test transaction is created correctly"""
        self.assertEqual(self.transaction.price, Decimal('100.00'))
        self.assertEqual(self.transaction.quantity, Decimal('2'))
        self.assertEqual(self.transaction.comment, 'Test comment')
        self.assertEqual(self.transaction.user, self.user)

    def test_transaction_str_with_unit(self):
        """Test transaction string representation with unit"""
        expected = f"{self.transaction.date} - Pizza (2 Pcs) [₹100.00] paid by John"
        self.assertEqual(str(self.transaction), expected)

    def test_transaction_str_without_quantity(self):
        """Test transaction string representation without quantity"""
        tx_no_qty = Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=50.00,
            date='2024-03-16'
        )
        expected = f"{tx_no_qty.date} - Pizza [₹50.00] paid by John"
        self.assertEqual(str(tx_no_qty), expected)

    def test_transaction_ordering(self):
        """Test transactions are ordered by date descending"""
        Transaction.objects.create(
            user=self.user,
            item=self.item,
            payer=self.payer,
            price=50.00,
            date='2024-03-16'
        )
        transactions = Transaction.objects.all()
        self.assertEqual(transactions[0].date.strftime('%Y-%m-%d'), '2024-03-16')

    def test_transaction_protected_delete_item(self):
        """Test item cannot be deleted if referenced by transaction"""
        with self.assertRaises(ProtectedError):
            self.item.delete()

    def test_transaction_protected_delete_payer(self):
        """Test payer cannot be deleted if referenced by transaction"""
        with self.assertRaises(ProtectedError):
            self.payer.delete()


class StagingTransactionModelTest(TestCase):
    """Test StagingTransaction model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.staging = StagingTransaction.objects.create(
            user=self.user,
            row_idx=1,
            date='2024-03-15',
            item_name='Pizza',
            price=100.00,
            quantity=2,
            payer_name='John',
            comment='Test',
            error=''
        )

    def test_staging_creation(self):
        """Test staging transaction is created correctly"""
        self.assertEqual(self.staging.user, self.user)
        self.assertEqual(self.staging.row_idx, 1)
        self.assertEqual(self.staging.item_name, 'Pizza')
        self.assertEqual(self.staging.price, 100.00)
        self.assertEqual(self.staging.error, '')

    def test_staging_fields_blank_allowed(self):
        """Test staging fields allow blank values"""
        staging_empty = StagingTransaction.objects.create(
            user=self.user,
            row_idx=2,
            date='2024-03-16'
        )
        self.assertEqual(staging_empty.item_name, '')
        self.assertEqual(staging_empty.payer_name, '')
        self.assertIsNone(staging_empty.quantity)
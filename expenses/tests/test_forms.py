from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from expenses.models import Category, Item, Payer
from expenses.forms import TransactionForm, ItemForm, PayerForm, ExcelUploadForm
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class TransactionFormTest(TestCase):
    """Test Transaction form"""

    def setUp(self):
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

    def test_valid_transaction_form(self):
        """Test form with valid data"""
        data = {
            'item': self.item.id,
            'payer': self.payer.id,
            'price': '100.00',
            'quantity': '2',
            'date': '2024-03-15',
            'comment': 'Test comment'
        }
        form = TransactionForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_transaction_form_without_user(self):
        """Test form without user (should not filter querysets)"""
        form = TransactionForm(data={})
        self.assertIn('item', form.fields)
        self.assertIn('payer', form.fields)

    def test_transaction_form_with_user_filters_querysets(self):
        """Test form with user filters item and payer querysets"""
        form = TransactionForm(user=self.user)
        self.assertIn(self.item, form.fields['item'].queryset)
        self.assertIn(self.payer, form.fields['payer'].queryset)

    def test_transaction_form_global_items_included(self):
        """Test global items are included in queryset"""
        global_item = Item.objects.create(
            name='Global Item',
            category=self.category,
            user=None
        )
        form = TransactionForm(user=self.user)
        self.assertIn(global_item, form.fields['item'].queryset)

    def test_invalid_transaction_form_empty_fields(self):
        """Test form with empty required fields"""
        data = {}
        form = TransactionForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('item', form.errors)
        self.assertIn('price', form.errors)
        self.assertIn('payer', form.errors)

    def test_invalid_transaction_form_negative_price(self):
        """Test form with negative price"""
        data = {
            'item': self.item.id,
            'payer': self.payer.id,
            'price': '-100.00',
            'quantity': '2',
            'date': '2024-03-15'
        }
        form = TransactionForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)

    def test_transaction_form_quantity_optional(self):
        """Test quantity field is optional"""
        data = {
            'item': self.item.id,
            'payer': self.payer.id,
            'price': '100.00',
            'date': '2024-03-15'
        }
        form = TransactionForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_transaction_form_comment_optional(self):
        """Test comment field is optional"""
        data = {
            'item': self.item.id,
            'payer': self.payer.id,
            'price': '100.00',
            'quantity': '2',
            'date': '2024-03-15'
        }
        form = TransactionForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())


class ItemFormTest(TestCase):
    """Test Item form"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Food')

    def test_valid_item_form(self):
        """Test form with valid data"""
        data = {
            'name': 'Pizza',
            'category': self.category.id,
            'unit': 'Pcs'
        }
        form = ItemForm(data=data)
        self.assertTrue(form.is_valid())

    def test_item_form_unit_optional(self):
        """Test unit field is optional"""
        data = {
            'name': 'Pizza',
            'category': self.category.id
        }
        form = ItemForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_item_form_empty_name(self):
        """Test form with empty name"""
        data = {
            'category': self.category.id
        }
        form = ItemForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class PayerFormTest(TestCase):
    """Test Payer form"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_valid_payer_form(self):
        """Test form with valid data"""
        data = {
            'name': 'John Doe',
            'color': '#FF0000'
        }
        form = PayerForm(data=data)
        self.assertTrue(form.is_valid())

    def test_payer_form_color_optional(self):
        """Test color field is optional"""
        data = {
            'name': 'John Doe'
        }
        form = PayerForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_payer_form_empty_name(self):
        """Test form with empty name"""
        data = {}
        form = PayerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class ExcelUploadFormTest(TestCase):
    """Test Excel Upload form"""

    def test_valid_excel_file(self):
        """Test form with valid Excel file"""
        file_content = b'test content'
        file = SimpleUploadedFile('test.xlsx', file_content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        data = {'excel_file': file}
        form = ExcelUploadForm(data=data, files={'excel_file': file})
        self.assertTrue(form.is_valid())

    def test_invalid_file_format(self):
        """Test form with invalid file format"""
        file = SimpleUploadedFile('test.txt', b'content', content_type='text/plain')
        data = {'excel_file': file}
        form = ExcelUploadForm(data=data, files={'excel_file': file})
        self.assertFalse(form.is_valid())
        self.assertIn('excel_file', form.errors)

    def test_missing_file(self):
        """Test form with missing file"""
        form = ExcelUploadForm(data={})
        self.assertFalse(form.is_valid())
from django.test import SimpleTestCase
from django.urls import reverse, resolve
from expenses import views


class TestUrls(SimpleTestCase):
    """Test URL patterns for expenses app"""

    def test_home_url_resolves(self):
        url = reverse('home')
        self.assertEqual(resolve(url).func.view_class, views.HomePageView)

    def test_transaction_list_url_resolves(self):
        url = reverse('transaction_list')
        self.assertEqual(resolve(url).func.view_class, views.TransactionListView)

    def test_create_transaction_url_resolves(self):
        url = reverse('create_transaction')
        self.assertEqual(resolve(url).func.view_class, views.TransactionCreateView)

    def test_update_transaction_url_resolves(self):
        url = reverse('update_transaction', args=[1])
        self.assertEqual(resolve(url).func.view_class, views.TransactionUpdateView)

    def test_delete_transaction_url_resolves(self):
        url = reverse('delete_transaction', args=[1])
        self.assertEqual(resolve(url).func.view_class, views.TransactionDeleteView)

    def test_create_payer_url_resolves(self):
        url = reverse('create_payer')
        self.assertEqual(resolve(url).func.view_class, views.PayerCreateView)

    def test_update_payer_url_resolves(self):
        url = reverse('update_payer', args=[1])
        self.assertEqual(resolve(url).func.view_class, views.PayerUpdateView)

    def test_delete_payer_url_resolves(self):
        url = reverse('delete_payer', args=[1])
        self.assertEqual(resolve(url).func.view_class, views.PayerDeleteView)

    def test_create_item_url_resolves(self):
        url = reverse('create_item')
        self.assertEqual(resolve(url).func.view_class, views.ItemCreateView)

    def test_update_item_url_resolves(self):
        url = reverse('update_item', args=[1])
        self.assertEqual(resolve(url).func.view_class, views.ItemUpdateView)

    def test_delete_item_url_resolves(self):
        url = reverse('delete_item', args=[1])
        self.assertEqual(resolve(url).func.view_class, views.ItemDeleteView)

    def test_bulk_upload_url_resolves(self):
        url = reverse('bulk_upload_transactions')
        self.assertEqual(resolve(url).func.view_class, views.TransactionBulkUploadView)

    def test_bulk_review_url_resolves(self):
        url = reverse('bulk_upload_review')
        self.assertEqual(resolve(url).func.view_class, views.TransactionBulkReviewView)

    def test_bulk_commit_url_resolves(self):
        url = reverse('bulk_upload_confirm_commit')
        self.assertEqual(resolve(url).func.view_class, views.BulkUploadCommitView)

    def test_bulk_delete_url_resolves(self):
        url = reverse('bulk_delete_transactions')
        self.assertEqual(resolve(url).func.view_class, views.TransactionBulkDeleteView)

    def test_manage_items_url_resolves(self):
        url = reverse('manage_items')
        self.assertEqual(resolve(url).func.view_class, views.ItemManagementListView)

    def test_manage_payers_url_resolves(self):
        url = reverse('manage_payers')
        self.assertEqual(resolve(url).func.view_class, views.PayerManagementListView)

    def test_delete_managed_item_url_resolves(self):
        url = reverse('delete_managed_item', args=[1])
        self.assertEqual(resolve(url).func.view_class, views.ItemDeleteView)

    def test_delete_managed_payer_url_resolves(self):
        url = reverse('delete_managed_payer', args=[1])
        self.assertEqual(resolve(url).func.view_class, views.PayerDeleteView)

    def test_all_url_names_exist(self):
        url_names = [
            'home', 'transaction_list', 'create_transaction',
            'update_transaction', 'delete_transaction',
            'create_payer', 'update_payer', 'delete_payer',
            'create_item', 'update_item', 'delete_item',
            'bulk_upload_transactions', 'bulk_upload_review',
            'bulk_upload_confirm_commit', 'bulk_delete_transactions',
            'manage_items', 'manage_payers',
            'delete_managed_item', 'delete_managed_payer'
        ]
        skip_names = [
            'update_transaction', 'delete_transaction',
            'update_payer', 'delete_payer',
            'update_item', 'delete_item',
            'delete_managed_item', 'delete_managed_payer'
        ]
        for name in url_names:
            if name in skip_names:
                continue
            try:
                reverse(name)
            except Exception as e:
                self.fail(f"URL name '{name}' does not exist: {e}")

    def test_home_url_path(self):
        self.assertEqual(reverse('home'), '/')

    def test_transaction_list_url_path(self):
        self.assertEqual(reverse('transaction_list'), '/transaction/')

    def test_create_transaction_url_path(self):
        self.assertEqual(reverse('create_transaction'), '/transaction/create/')

    def test_update_transaction_url_path(self):
        self.assertEqual(reverse('update_transaction', args=[1]), '/transaction/edit/1/')

    def test_delete_transaction_url_path(self):
        self.assertEqual(reverse('delete_transaction', args=[1]), '/transaction/delete/1/')

    def test_manage_items_url_path(self):
        self.assertEqual(reverse('manage_items'), '/items/manage/')

    def test_manage_payers_url_path(self):
        self.assertEqual(reverse('manage_payers'), '/payers/manage/')
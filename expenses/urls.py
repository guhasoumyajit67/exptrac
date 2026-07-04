from django.urls import path
from .views import (
    HomePageView,
    TransactionCreateView,
    TransactionListView,
    TransactionUpdateView,  
    TransactionDeleteView,  
    ItemCreateView,
    ItemUpdateView,    # Added for editing items
    ItemDeleteView,    # Added for deleting items
    PayerCreateView,
    PayerUpdateView,   # Added for editing payers
    PayerDeleteView,   # Added for deleting payers
    TransactionBulkUploadView,
    TransactionBulkReviewView,
    BulkUploadCommitView,
    TransactionBulkDeleteView
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("transaction/", TransactionListView.as_view(), name="transaction_list"),
    path("transaction/create/", TransactionCreateView.as_view(), name="create_transaction"),
    
    # Dedicated separate Transaction CRUD routing paths
    path("transaction/edit/<int:pk>/", TransactionUpdateView.as_view(), name="update_transaction"),
    path("transaction/delete/<int:pk>/", TransactionDeleteView.as_view(), name="delete_transaction"),
    
    # Payer CRUD Routing Parameters
    path("payer/create/", PayerCreateView.as_view(), name="create_payer"),
    path("payer/<int:pk>/update/", PayerUpdateView.as_view(), name="update_payer"),
    path("payer/<int:pk>/delete/", PayerDeleteView.as_view(), name="delete_payer"),
    
    # Custom Item CRUD Routing Parameters
    path("item/create/", ItemCreateView.as_view(), name="create_item"),
    path("item/<int:pk>/update/", ItemUpdateView.as_view(), name="update_item"),
    path("item/<int:pk>/delete/", ItemDeleteView.as_view(), name="delete_item"),

    # Bulk upload
    path('transaction/bulk-upload/', TransactionBulkUploadView.as_view(), name='bulk_upload_transactions'),
    path('transaction/bulk-review/', TransactionBulkReviewView.as_view(), name='bulk_upload_review'),
    path('transaction/bulk-commit/', BulkUploadCommitView.as_view(), name='bulk_upload_confirm_commit'),

    # Bulk Delete
    path('transaction/bulk-delete/', TransactionBulkDeleteView.as_view(), name='bulk_delete_transactions'),
]
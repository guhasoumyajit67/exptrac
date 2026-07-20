from django.urls import path
from .views import (
    HomePageView,
    TransactionCreateView,
    TransactionListView,
    TransactionUpdateView,  
    TransactionDeleteView,  
    ItemCreateView,
    ItemUpdateView,    
    ItemDeleteView,    
    PayerCreateView,
    PayerUpdateView,   
    PayerDeleteView,   
    TransactionBulkUploadView,
    TransactionBulkReviewView,
    BulkUploadCommitView,
    TransactionBulkDeleteView,
    ItemManagementListView,
    PayerManagementListView,
    TransactionExportView,  # Add this import
)

urlpatterns = [
    # Home & Core Transactions
    path("", HomePageView.as_view(), name="home"),
    path("transaction/", TransactionListView.as_view(), name="transaction_list"),
    path("transaction/create/", TransactionCreateView.as_view(), name="create_transaction"),
    
    # Dedicated Separate Transaction CRUD Routing Paths
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

    # Bulk Operations
    path('transaction/bulk-upload/', TransactionBulkUploadView.as_view(), name='bulk_upload_transactions'),
    path('transaction/bulk-review/', TransactionBulkReviewView.as_view(), name='bulk_upload_review'),
    path('transaction/bulk-commit/', BulkUploadCommitView.as_view(), name='bulk_upload_confirm_commit'),
    path('transaction/bulk-delete/', TransactionBulkDeleteView.as_view(), name='bulk_delete_transactions'),

    # Configuration Dashboard List Views
    path("items/manage/", ItemManagementListView.as_view(), name="manage_items"),
    path("payers/manage/", PayerManagementListView.as_view(), name="manage_payers"),

    # Consolidated Dashboard Deletion Target URIs
    path("items/manage/<int:pk>/delete/", ItemDeleteView.as_view(), name="delete_managed_item"),
    path("payers/manage/<int:pk>/delete/", PayerDeleteView.as_view(), name="delete_managed_payer"),

    # Export
    path('transaction/export/', TransactionExportView.as_view(), name='export_transactions'),  # Add this
]
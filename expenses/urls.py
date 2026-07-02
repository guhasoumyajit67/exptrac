from django.urls import path
from .views import (
    HomePageView,
    TransactionCreateView,
    TransactionListView,
    TransactionUpdateView,  # Added
    TransactionDeleteView,  # Added
    ItemCreateView,
    PayerCreateView,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("transaction/", TransactionListView.as_view(), name="transaction_list"),
    path("transaction/create/", TransactionCreateView.as_view(), name="create_transaction"),
    
    # Dedicated separate CRUD routing paths
    path("transaction/edit/<int:pk>/", TransactionUpdateView.as_view(), name="update_transaction"),
    path("transaction/delete/<int:pk>/", TransactionDeleteView.as_view(), name="delete_transaction"),
    
    path("item/create/", ItemCreateView.as_view(), name="create_item"),
    path("payer/create/", PayerCreateView.as_view(), name="create_payer"),
] # Don't forget to close the bracket!

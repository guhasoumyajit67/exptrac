from django.urls import path
from .views import (
    HomePageView,
    TransactionCreateView,
    TransactionListView,
    ItemCreateView,
    PayerCreateView,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("transaction/", TransactionListView.as_view(), name="transaction_list"),
    path("transaction/create/", TransactionCreateView.as_view(), name="create_transaction"),
    path("item/create/", ItemCreateView.as_view(), name="create_item"),
    path("payer/create/", PayerCreateView.as_view(), name="create_payer"),
]


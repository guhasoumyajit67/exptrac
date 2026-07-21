# analytics/urls.py
from django.urls import path
from .views import DashboardAnalyticsView, ExportAnalyticsPDFView

urlpatterns = [
    # This creates the URL name 'analytics_dashboard'
    path('dashboard/', DashboardAnalyticsView.as_view(), name='analytics_dashboard'),
    path('dashboard/export-analytics-pdf/', ExportAnalyticsPDFView.as_view(), name='export_analytics_pdf'),
]
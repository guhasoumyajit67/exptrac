from django.test import SimpleTestCase
from django.urls import reverse, resolve
from analytics.views import DashboardAnalyticsView, ExportAnalyticsPDFView


class TestUrls(SimpleTestCase):
    """Test URL patterns for analytics app"""

    def test_analytics_dashboard_url_resolves(self):
        """Test analytics dashboard URL resolves to DashboardAnalyticsView"""
        url = reverse('analytics_dashboard')
        self.assertEqual(resolve(url).func.view_class, DashboardAnalyticsView)

    def test_analytics_dashboard_url_path(self):
        """Test analytics dashboard URL path is correct"""
        self.assertEqual(reverse('analytics_dashboard'), '/analytics/dashboard/')

    def test_export_analytics_pdf_url_resolves(self):
        """Test export analytics PDF URL resolves to ExportAnalyticsPDFView"""
        url = reverse('export_analytics_pdf')
        self.assertEqual(resolve(url).func.view_class, ExportAnalyticsPDFView)

    def test_export_analytics_pdf_url_path(self):
        """Test export analytics PDF URL path is correct"""
        self.assertEqual(reverse('export_analytics_pdf'), '/analytics/dashboard/export-analytics-pdf/')

from django.test import SimpleTestCase
from django.urls import reverse, resolve
from analytics.views import DashboardAnalyticsView


class TestUrls(SimpleTestCase):
    """Test URL patterns for analytics app"""

    def test_dashboard_analytics_url_resolves(self):
        """Test dashboard analytics URL resolves to DashboardAnalyticsView"""
        url = reverse('dashboard_analytics')
        self.assertEqual(resolve(url).func.view_class, DashboardAnalyticsView)

    def test_dashboard_analytics_url_path(self):
        """Test dashboard analytics URL path is correct"""
        self.assertEqual(reverse('dashboard_analytics'), '/analytics/dashboard/')
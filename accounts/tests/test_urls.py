from django.test import SimpleTestCase
from django.urls import reverse, resolve
from accounts.views import SignUpView


class TestUrls(SimpleTestCase):
    """Test URL patterns for accounts app"""

    def test_signup_url_resolves(self):
        """Test signup URL resolves to SignUpView"""
        url = reverse('signup')
        self.assertEqual(resolve(url).func.view_class, SignUpView)

    def test_signup_url_path(self):
        """Test signup URL path is correct"""
        self.assertEqual(reverse('signup'), '/accounts/signup/')

    def test_login_url(self):
        """Test login URL exists"""
        url = reverse('login')
        self.assertEqual(url, '/accounts/login/')

    def test_logout_url(self):
        """Test logout URL exists"""
        url = reverse('logout')
        self.assertEqual(url, '/accounts/logout/')

    def test_password_reset_url(self):
        """Test password reset URL exists"""
        url = reverse('password_reset')
        self.assertEqual(url, '/accounts/password_reset/')

    def test_password_reset_done_url(self):
        """Test password reset done URL exists"""
        url = reverse('password_reset_done')
        self.assertEqual(url, '/accounts/password_reset/done/')

    def test_password_reset_confirm_url(self):
        """Test password reset confirm URL exists"""
        url = reverse('password_reset_confirm', kwargs={'uidb64': 'uid', 'token': 'token'})
        self.assertEqual(url, '/accounts/reset/uid/token/')
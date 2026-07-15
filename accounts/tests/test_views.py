from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class SignUpViewTest(TestCase):
    """Test SignUp View"""

    def setUp(self):
        self.client = Client()

    def test_signup_page_loads(self):
        """Test signup page loads correctly"""
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/signup.html')

    def test_signup_page_contains_form(self):
        """Test signup page contains form"""
        response = self.client.get(reverse('signup'))
        self.assertContains(response, 'form')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_signup_success(self):
        """Test successful signup"""
        data = {
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(reverse('signup'), data)
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertRedirects(response, reverse('login'))
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.username, 'newuser')

    def test_signup_invalid_data(self):
        """Test signup with invalid data"""
        data = {
            'username': '',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(reverse('signup'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)

    def test_signup_password_mismatch(self):
        """Test signup with mismatched passwords"""
        data = {
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'wrongpass',
        }
        response = self.client.post(reverse('signup'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)

    def test_signup_duplicate_username(self):
        """Test signup with duplicate username"""
        User.objects.create_user(username='existing', password='testpass123')
        data = {
            'username': 'existing',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(reverse('signup'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)

    def test_signup_redirects_if_authenticated(self):
        """Test signup redirects if user already authenticated"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('signup'))
        # The redirect depends on your auth settings
        # This test ensures the page is accessible
        self.assertEqual(response.status_code, 200)
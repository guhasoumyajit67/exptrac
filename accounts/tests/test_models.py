from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserModelTest(TestCase):
    """Test CustomUser model"""

    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_user_str_method(self):
        """Test user string representation"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(str(user), 'testuser')

    def test_user_email_optional(self):
        """Test user email is optional"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(user.email, '')

    def test_user_username_required(self):
        """Test username is required"""
        with self.assertRaises(TypeError):
            User.objects.create_user(password='testpass123')
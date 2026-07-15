from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.forms import CustomUserCreationForm, CustomUserChangeForm

User = get_user_model()


class CustomUserCreationFormTest(TestCase):
    """Test CustomUserCreationForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        data = {
            'username': 'testuser',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        form = CustomUserCreationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_passwords_mismatch(self):
        """Test form with mismatched passwords"""
        data = {
            'username': 'testuser',
            'password1': 'testpass123',
            'password2': 'wrongpass',
        }
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_invalid_form_username_empty(self):
        """Test form with empty username"""
        data = {
            'username': '',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_invalid_form_username_duplicate(self):
        """Test form with duplicate username"""
        User.objects.create_user(username='testuser', password='testpass123')
        data = {
            'username': 'testuser',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        form = CustomUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_form_saves_user(self):
        """Test form saves user correctly"""
        data = {
            'username': 'newuser',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        form = CustomUserCreationForm(data=data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertTrue(user.check_password('testpass123'))

    def test_form_uses_custom_user_model(self):
        """Test form uses CustomUser model"""
        form = CustomUserCreationForm()
        self.assertEqual(form._meta.model, User)


class CustomUserChangeFormTest(TestCase):
    """Test CustomUserChangeForm"""

    def test_form_uses_custom_user_model(self):
        """Test form uses CustomUser model"""
        form = CustomUserChangeForm()
        self.assertEqual(form._meta.model, User)

    def test_form_fields(self):
        """Test form has expected fields"""
        form = CustomUserChangeForm()
        expected_fields = ['username', 'first_name', 'last_name', 'email']
        for field in expected_fields:
            self.assertIn(field, form.fields)
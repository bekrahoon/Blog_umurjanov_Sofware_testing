from users.models import CustomUser
from users.tests.helpers import PASSWORD, UsersBaseTestCase, make_photo


class RegisterTests(UsersBaseTestCase):
    """Тесты регистрации /register/"""

    def valid_data(self, **changes):
        data = {
            'username': 'newuser',
            'password1': PASSWORD,
            'password2': PASSWORD,
            'first_name': 'Ivan',
            'email': 'ivan@gmail.com',
            'phone_number': '+996444222111',
            'date_bir': '1999-05-05',
            'gender': 'MALE',
            'city': 'Tokmok',
            'photo': make_photo('new.gif'),
        }
        data.update(changes)
        return data

    def test_register_page_opens(self):
        """Страница регистрации открывается (200) и использует шаблон users/register.html"""
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_register_success(self):
        """Успешная регистрация: редирект на /login/, пользователь создан со всеми полями"""
        response = self.client.post('/register/', self.valid_data())
        self.assertRedirects(response, '/login/')
        self.assertEqual(CustomUser.objects.count(), 2)
        user = CustomUser.objects.get(username='newuser')
        self.assertEqual(user.city, 'Tokmok')
        self.assertEqual(user.phone_number, '+996444222111')
        self.assertTrue(user.check_password(PASSWORD))

    def test_register_passwords_mismatch(self):
        """Пароли не совпадают — пользователь не создаётся, форма с ошибкой"""
        response = self.client.post('/register/', self.valid_data(password2='OtherPassword456'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('password2', response.context['form'].errors)
        self.assertFalse(CustomUser.objects.filter(username='newuser').exists())

    def test_register_duplicate_username(self):
        """Логин уже занят — повторная регистрация невозможна"""
        response = self.client.post('/register/', self.valid_data(username='testuser'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.context['form'].errors)
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_register_without_photo(self):
        """Фото обязательно — без фото регистрация не проходит"""
        data = self.valid_data()
        data.pop('photo')
        response = self.client.post('/register/', data)
        self.assertIn('photo', response.context['form'].errors)
        self.assertFalse(CustomUser.objects.filter(username='newuser').exists())

    def test_register_invalid_email(self):
        """Неверный формат email — ошибка в поле email"""
        response = self.client.post('/register/', self.valid_data(email='not-an-email'))
        self.assertIn('email', response.context['form'].errors)
        self.assertFalse(CustomUser.objects.filter(username='newuser').exists())

    def test_register_weak_password(self):
        """Слишком простой пароль (12345678) отклоняется валидаторами Django"""
        response = self.client.post('/register/', self.valid_data(password1='12345678', password2='12345678'))
        self.assertIn('password2', response.context['form'].errors)
        self.assertFalse(CustomUser.objects.filter(username='newuser').exists())

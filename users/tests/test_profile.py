from users.tests.helpers import UsersBaseTestCase


class ProfileTests(UsersBaseTestCase):
    """Тесты личного кабинета /profile/"""

    def test_profile_requires_login(self):
        """Гость не может открыть кабинет — редирект на /login/?next=/profile/"""
        response = self.client.get('/profile/')
        self.assertRedirects(response, '/login/?next=/profile/')

    def test_profile_opens_for_user(self):
        """Авторизованный пользователь видит кабинет (200, шаблон users/profile.html)"""
        self.client.force_login(self.user)
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_profile_shows_user_data(self):
        """В кабинете выводятся данные пользователя: логин, имя, почта, город, телефон"""
        self.client.force_login(self.user)
        response = self.client.get('/profile/')
        for text in ('testuser', 'Test', 'test@gmail.com', 'Bishkek', '+996333222111'):
            self.assertContains(response, text)

    def test_profile_hides_password_hash(self):
        """Хеш пароля не показывается в кабинете"""
        self.client.force_login(self.user)
        response = self.client.get('/profile/')
        self.assertNotContains(response, self.user.password)

    def test_profile_shows_only_own_data(self):
        """Каждый пользователь видит только свой кабинет"""
        from users.models import CustomUser
        from users.tests.helpers import make_photo
        other = CustomUser.objects.create_user(
            username='otheruser', password='StrongPassword123', email='other@gmail.com',
            phone_number='+996555000111', date_bir='2001-02-02', gender='FEMALE',
            city='Osh', photo=make_photo('other.gif'),
        )
        self.client.force_login(other)
        response = self.client.get('/profile/')
        self.assertContains(response, 'otheruser')
        self.assertNotContains(response, 'test@gmail.com')

    def test_full_flow_register_login_profile(self):
        """Полный сценарий: регистрация → вход с капчей → личный кабинет"""
        from users.tests.helpers import PASSWORD, make_photo
        self.client.post('/register/', {
            'username': 'flowuser', 'password1': PASSWORD, 'password2': PASSWORD,
            'first_name': 'Aba', 'email': 'flow@gmail.com', 'phone_number': '+996700000000',
            'date_bir': '2005-10-16', 'gender': 'MALE', 'city': 'Tokmok',
            'photo': make_photo('flow.gif'),
        })
        response = self.client.post('/login/', self.login_data(username='flowuser'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Личный кабинет: flowuser')

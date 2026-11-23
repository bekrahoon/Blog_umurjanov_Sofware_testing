from users.tests.helpers import UsersBaseTestCase


class LoginTests(UsersBaseTestCase):
    """Тесты авторизации /login/ (вход всегда идёт вместе с капчей)"""

    def test_login_page_opens(self):
        """Страница входа открывается (200), шаблон users/login.html, в форме есть поле captcha"""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')
        self.assertIn('captcha', response.context['form'].fields)

    def test_login_success(self):
        """Верный логин, пароль и капча — вход выполнен, редирект на /profile/"""
        response = self.client.post('/login/', self.login_data())
        self.assertRedirects(response, '/profile/')
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.id)

    def test_login_wrong_password(self):
        """Неверный пароль (капча верная) — вход не выполнен"""
        response = self.client.post('/login/', self.login_data(password='WrongPass999'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_unknown_user(self):
        """Несуществующий пользователь — вход не выполнен"""
        response = self.client.post('/login/', self.login_data(username='nobody'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout(self):
        """Выход: редирект на /login/, сессия очищена, кабинет снова закрыт"""
        self.client.force_login(self.user)
        response = self.client.post('/logout/')
        self.assertRedirects(response, '/login/')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertRedirects(self.client.get('/profile/'), '/login/?next=/profile/')

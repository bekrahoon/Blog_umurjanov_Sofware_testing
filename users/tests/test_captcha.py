from captcha.models import CaptchaStore

from users.tests.helpers import UsersBaseTestCase


class CaptchaTests(UsersBaseTestCase):
    """Тесты капчи на странице входа"""

    def test_captcha_shown_on_login_page(self):
        """На странице входа есть картинка капчи и поля captcha_0 / captcha_1"""
        response = self.client.get('/login/')
        self.assertContains(response, 'class="captcha"')
        self.assertContains(response, 'name="captcha_0"')
        self.assertContains(response, 'name="captcha_1"')

    def test_captcha_created_in_db(self):
        """При открытии страницы входа в БД создаётся новая капча"""
        before = CaptchaStore.objects.count()
        self.client.get('/login/')
        self.assertEqual(CaptchaStore.objects.count(), before + 1)

    def test_captcha_image_is_png(self):
        """Картинка капчи отдаётся по /captcha/image/<hashkey>/ как PNG"""
        hashkey, _ = self.get_captcha()
        response = self.client.get(f'/captcha/image/{hashkey}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')

    def test_login_wrong_captcha(self):
        """Верный логин и пароль, но неверная капча — вход НЕ выполнен, ошибка в поле captcha"""
        response = self.client.post('/login/', self.login_data(wrong_captcha=True))
        self.assertEqual(response.status_code, 200)
        self.assertIn('captcha', response.context['form'].errors)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_without_captcha(self):
        """Капча не заполнена — вход НЕ выполнен"""
        response = self.client.post('/login/', self.login_data(captcha=False))
        self.assertEqual(response.status_code, 200)
        self.assertIn('captcha', response.context['form'].errors)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_captcha_case_insensitive(self):
        """Капча принимается и в верхнем регистре"""
        data = self.login_data()
        data['captcha_1'] = data['captcha_1'].upper()
        response = self.client.post('/login/', data)
        self.assertRedirects(response, '/profile/')

    def test_captcha_cannot_be_reused(self):
        """Одну и ту же капчу нельзя использовать второй раз"""
        data = self.login_data()
        self.client.post('/login/', data)
        self.client.logout()
        response = self.client.post('/login/', data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('captcha', response.context['form'].errors)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_fake_captcha_key(self):
        """Поддельный hashkey капчи — вход НЕ выполнен"""
        data = self.login_data()
        data['captcha_0'] = '0' * 40
        response = self.client.post('/login/', data)
        self.assertIn('captcha', response.context['form'].errors)
        self.assertNotIn('_auth_user_id', self.client.session)

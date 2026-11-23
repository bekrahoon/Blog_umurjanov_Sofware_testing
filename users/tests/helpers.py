"""Общие помощники для тестов users: картинка-заглушка, пользователь, решение капчи."""
import re
import tempfile

from captcha.models import CaptchaStore
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from users.models import CustomUser

PASSWORD = 'StrongPassword123'

# минимальный валидный GIF 1x1
GIF = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04'
    b'\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


def make_photo(name='test.gif'):
    return SimpleUploadedFile(name, GIF, content_type='image/gif')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class UsersBaseTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password=PASSWORD,
            first_name='Test',
            email='test@gmail.com',
            phone_number='+996333222111',
            date_bir='2000-01-01',
            gender='MALE',
            city='Bishkek',
            photo=make_photo('user.gif'),
        )

    def get_captcha(self):
        """Открывает /login/ и возвращает (hashkey, правильный ответ) капчи с этой страницы."""
        response = self.client.get('/login/')
        hashkey = re.search(r'name="captcha_0" value="([0-9a-f]+)"', response.content.decode()).group(1)
        answer = CaptchaStore.objects.get(hashkey=hashkey).response
        return hashkey, answer

    def login_data(self, username='testuser', password=PASSWORD, captcha=True, wrong_captcha=False):
        data = {'username': username, 'password': password}
        if captcha:
            hashkey, answer = self.get_captcha()
            data['captcha_0'] = hashkey
            data['captcha_1'] = 'WRONG' if wrong_captcha else answer
        return data

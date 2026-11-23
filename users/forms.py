from captcha.fields import CaptchaField
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from users.models import CustomUser

GENDER = (
    ('MALE', 'MALE'),
    ('FEMALE', 'FEMALE'),
)


class CustomRegisterForm(UserCreationForm):
    photo = forms.ImageField(required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True, initial='+996')
    date_bir = forms.DateField(required=True)
    gender = forms.ChoiceField(choices=GENDER, required=True)
    city = forms.CharField(max_length=100, required=True)

    class Meta:
        model = CustomUser
        fields = (
            'username', 'password1', 'password2', 'first_name', 'photo',
            'email', 'phone_number', 'date_bir', 'gender', 'city',
        )


class CaptchaLoginForm(AuthenticationForm):
    """Обычная форма входа Django + капча (django-simple-captcha)."""
    captcha = CaptchaField(label='Введите текст с картинки')

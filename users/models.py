from django.db import models
from django.contrib.auth.models import User


class CustomUser(User):
    GENDER = (
        ('MALE', 'MALE'),
        ('FEMALE', 'FEMALE'),
    )
    photo = models.ImageField(upload_to='users/')
    phone_number = models.CharField(max_length=15)
    date_bir = models.DateField()
    gender = models.CharField(max_length=100, choices=GENDER)
    city = models.CharField(max_length=100)

    def __str__(self):
        return self.username

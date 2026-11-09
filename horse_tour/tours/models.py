"""
Модели стартапа «Конный тур» (Horse Tour).

Связи между моделями:

* **Многие ко многим** — :model:`tours.Tour` <-> :model:`tours.Category`
  (у тура может быть несколько категорий: «конный», «пеший», «мото»).
* **Один к одному** — :model:`tours.Tour` <-> :model:`tours.TourRoute`
  (у каждого тура ровно один маршрут).
* **Один ко многим** — :model:`tours.Customer` -> :model:`tours.Booking`,
  :model:`tours.Tour` -> :model:`tours.Booking`,
  :model:`tours.Customer` -> :model:`tours.Comment`,
  :model:`tours.Tour` -> :model:`tours.Comment`.
"""
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


# Многие ко многим (через Tour.categories)
class Category(models.Model):
    """
    Категория тура, например «конный», «пеший» или «мото».

    Связана с :model:`tours.Tour` отношением многие ко многим.
    """
    name = models.CharField('Название', max_length=50, unique=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Tour(models.Model):
    """
    Тур, который продаёт стартап.

    * ``categories`` — многие ко многим с :model:`tours.Category`;
    * ``route`` — обратная связь один к одному с :model:`tours.TourRoute`;
    * ``bookings`` / ``comments`` — обратные связи один ко многим.
    """
    title = models.CharField('Название', max_length=100)
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField(
        'Цена (сом)', max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    duration_hours = models.PositiveIntegerField(
        'Длительность (часы)', default=3,
        validators=[MinValueValidator(1), MaxValueValidator(240)],
    )
    categories = models.ManyToManyField(
        Category, related_name='tours', verbose_name='Категории',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Тур'
        verbose_name_plural = 'Туры'
        ordering = ['-id']

    def __str__(self):
        return self.title


# Один к одному
class TourRoute(models.Model):
    """
    Маршрут тура. Каждый :model:`tours.Tour` имеет ровно один маршрут
    (связь один к одному).
    """
    tour = models.OneToOneField(
        Tour, on_delete=models.CASCADE, related_name='route', verbose_name='Тур',
    )
    start_point = models.CharField('Точка старта', max_length=100)
    end_point = models.CharField('Точка финиша', max_length=100)
    distance_km = models.DecimalField(
        'Расстояние (км)', max_digits=6, decimal_places=1,
        validators=[MinValueValidator(0.1)],
    )

    class Meta:
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршруты'

    def __str__(self):
        return f'{self.tour}: {self.start_point} → {self.end_point}'


class Customer(models.Model):
    """
    Клиент (человек), который покупает туры и оставляет комментарии.

    Связан один ко многим с :model:`tours.Booking` и :model:`tours.Comment`.
    """
    full_name = models.CharField('ФИО', max_length=100)
    phone = models.CharField('Телефон', max_length=20, unique=True)
    email = models.EmailField('Email', blank=True)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


# Один ко многим
class Booking(models.Model):
    """
    Покупка (бронь) тура клиентом.

    Правило: **один человек может купить только один тур на определённый
    день и время** — уникальность по (``customer``, ``date``, ``time``).
    """
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='bookings',
        verbose_name='Клиент',
    )
    tour = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name='bookings', verbose_name='Тур',
    )
    date = models.DateField('Дата')
    time = models.TimeField('Время')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Покупка тура'
        verbose_name_plural = 'Покупки туров'
        ordering = ['-date', '-time']
        constraints = [
            models.UniqueConstraint(
                fields=['customer', 'date', 'time'],
                name='one_tour_per_customer_per_datetime',
                violation_error_message=(
                    'Этот человек уже купил тур на этот день и время.'
                ),
            ),
        ]

    def __str__(self):
        return f'{self.customer} — {self.tour} ({self.date} {self.time:%H:%M})'


# Один ко многим
class Comment(models.Model):
    """
    Комментарий клиента к туру.

    Правило: **человек может оставить несколько комментариев, но только к
    турам, в которых он был** — т.е. у него есть :model:`tours.Booking`
    на этот тур с датой не позже сегодняшней.
    """
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='comments',
        verbose_name='Клиент',
    )
    tour = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name='comments', verbose_name='Тур',
    )
    text = models.TextField('Текст')
    mark = models.PositiveSmallIntegerField(
        'Оценка', default=5, validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.customer} → {self.tour}: {self.mark}'

    def clean(self):
        """Проверяет, что клиент действительно был на этом туре."""
        super().clean()
        if self.customer_id and self.tour_id:
            was_on_tour = Booking.objects.filter(
                customer_id=self.customer_id,
                tour_id=self.tour_id,
                date__lte=timezone.localdate(),
            ).exists()
            if not was_on_tour:
                raise ValidationError(
                    'Можно комментировать только туры, в которых вы были.'
                )

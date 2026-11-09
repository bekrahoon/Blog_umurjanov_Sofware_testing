"""
Тесты стартапа «Конный тур».

Проверяется:
1. Связи 1 к 1, 1 ко многим, многие ко многим.
2. Правило: 1 человек может купить только 1 тур на определённый день и время.
3. Правило: 1 человек может оставить несколько комментариев к турам, в которых был.
4. Категории тура: «конный», «пеший», «мото».
5. Все отправки данных (POST всех форм) — валидные и невалидные.
6. Документация через django.contrib.admindocs.

После прогона автоматически создаётся отчёт Test_Report.docx.
"""
import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from tours.models import Booking, Category, Comment, Customer, Tour, TourRoute

REPORT_PATH = 'Test_Report.docx'
REPORT_ROWS = []

TODAY = timezone.localdate()
YESTERDAY = TODAY - datetime.timedelta(days=1)
TOMORROW = TODAY + datetime.timedelta(days=1)
TEN_AM = datetime.time(10, 0)
TWO_PM = datetime.time(14, 0)


def tearDownModule():
    """Сохраняет отчёт о тестировании в Word."""
    doc = Document()
    title = doc.add_paragraph()
    run = title.add_run('Отчет об автоматическом тестировании')
    run.font.name = 'Arial'
    run.font.size = Pt(18)
    run.font.bold = True
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('Проект: Horse Tour — стартап «Конный тур» (Django)')
    passed = sum(1 for r in REPORT_ROWS if r[3] == 'Успешно!')
    doc.add_paragraph(f'Всего тестов: {len(REPORT_ROWS)}, успешно: {passed}')

    table = doc.add_table(rows=1, cols=4)
    table.style = 'Table Grid'
    for cell, text in zip(table.rows[0].cells, ['Группа', 'Тест', 'Что проверяется', 'Результат']):
        cell.text = text
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.bold = True
    for row in REPORT_ROWS:
        cells = table.add_row().cells
        for cell, text in zip(cells, row):
            cell.text = text
    doc.save(REPORT_PATH)


class ReportMixin:
    """Записывает результат каждого теста в отчёт (как в примере TestingPO)."""

    def tearDown(self):
        result = self._outcome.result
        failed = any(t is self for t, _ in result.failures + result.errors)
        doc = (self._testMethodDoc or '').strip().splitlines()
        REPORT_ROWS.append((
            self.__class__.__doc__.strip().splitlines()[0] if self.__class__.__doc__ else self.__class__.__name__,
            self._testMethodName,
            doc[0] if doc else '',
            'Ошибка!' if failed else 'Успешно!',
        ))
        super().tearDown()


class BaseTourTestCase(ReportMixin, TestCase):
    """Общие тестовые данные."""

    def setUp(self):
        self.horse = Category.objects.create(name='конный')
        self.walk = Category.objects.create(name='пеший')
        self.moto = Category.objects.create(name='мото')

        self.tour = Tour.objects.create(
            title='Сон-Куль на лошадях', description='Тур к озеру Сон-Куль',
            price=5000, duration_hours=8,
        )
        self.tour.categories.add(self.horse, self.walk)

        self.tour2 = Tour.objects.create(title='Мото по Чуйской долине', price=7000)
        self.tour2.categories.add(self.moto)

        self.customer = Customer.objects.create(
            full_name='Иванов Иван', phone='+996700000001', email='ivan@mail.kg',
        )
        self.customer2 = Customer.objects.create(
            full_name='Петров Пётр', phone='+996700000002',
        )


# ---------------------------------------------------------------------------
# 1. Связи
# ---------------------------------------------------------------------------
class RelationsTests(BaseTourTestCase):
    """Связи 1 к 1, 1 ко многим, многие ко многим"""

    def test_str_methods(self):
        """__str__ у всех моделей"""
        route = TourRoute.objects.create(tour=self.tour, start_point='Кочкор',
                                         end_point='Сон-Куль', distance_km=40)
        booking = Booking.objects.create(customer=self.customer, tour=self.tour,
                                         date=YESTERDAY, time=TEN_AM)
        comment = Comment.objects.create(customer=self.customer, tour=self.tour,
                                         text='Супер', mark=5)
        self.assertEqual(str(self.horse), 'конный')
        self.assertEqual(str(self.tour), 'Сон-Куль на лошадях')
        self.assertEqual(str(self.customer), 'Иванов Иван')
        self.assertEqual(str(route), 'Сон-Куль на лошадях: Кочкор → Сон-Куль')
        self.assertIn('Иванов Иван — Сон-Куль на лошадях', str(booking))
        self.assertEqual(str(comment), 'Иванов Иван → Сон-Куль на лошадях: 5')

    def test_one_to_one_route(self):
        """1 к 1: у тура ровно один маршрут, доступ tour.route"""
        route = TourRoute.objects.create(tour=self.tour, start_point='Кочкор',
                                         end_point='Сон-Куль', distance_km=40)
        self.assertEqual(self.tour.route, route)
        self.assertEqual(route.tour, self.tour)

    def test_one_to_one_second_route_forbidden(self):
        """1 к 1: второй маршрут для того же тура запрещён"""
        TourRoute.objects.create(tour=self.tour, start_point='A', end_point='B', distance_km=1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TourRoute.objects.create(tour=self.tour, start_point='C',
                                         end_point='D', distance_km=2)

    def test_one_to_one_cascade_delete(self):
        """1 к 1: при удалении тура удаляется маршрут"""
        TourRoute.objects.create(tour=self.tour, start_point='A', end_point='B', distance_km=1)
        self.tour.delete()
        self.assertEqual(TourRoute.objects.count(), 0)

    def test_one_to_many_bookings(self):
        """1 ко многим: у клиента и у тура может быть много покупок"""
        Booking.objects.create(customer=self.customer, tour=self.tour, date=TODAY, time=TEN_AM)
        Booking.objects.create(customer=self.customer, tour=self.tour2, date=TOMORROW, time=TEN_AM)
        Booking.objects.create(customer=self.customer2, tour=self.tour, date=TODAY, time=TEN_AM)
        self.assertEqual(self.customer.bookings.count(), 2)
        self.assertEqual(self.tour.bookings.count(), 2)

    def test_one_to_many_cascade_delete(self):
        """1 ко многим: при удалении клиента удаляются его покупки"""
        Booking.objects.create(customer=self.customer, tour=self.tour, date=TODAY, time=TEN_AM)
        self.customer.delete()
        self.assertEqual(Booking.objects.count(), 0)

    def test_many_to_many_categories(self):
        """Многие ко многим: тур в нескольких категориях и категория у нескольких туров"""
        self.tour2.categories.add(self.horse)
        self.assertEqual(set(self.tour.categories.all()), {self.horse, self.walk})
        self.assertEqual(set(self.horse.tours.all()), {self.tour, self.tour2})

    def test_many_to_many_remove(self):
        """Многие ко многим: удаление категории у тура не удаляет сам тур"""
        self.tour.categories.remove(self.walk)
        self.assertEqual(list(self.tour.categories.all()), [self.horse])
        self.walk.delete()
        self.assertTrue(Tour.objects.filter(id=self.tour.id).exists())


# ---------------------------------------------------------------------------
# 2. Один человек — один тур на день и время
# ---------------------------------------------------------------------------
class BookingRuleTests(BaseTourTestCase):
    """1 человек — только 1 тур на определённый день и время"""

    def test_same_customer_same_datetime_db_error(self):
        """Тот же человек, тот же день и время, другой тур — ошибка БД"""
        Booking.objects.create(customer=self.customer, tour=self.tour, date=TOMORROW, time=TEN_AM)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Booking.objects.create(customer=self.customer, tour=self.tour2,
                                       date=TOMORROW, time=TEN_AM)

    def test_same_customer_same_datetime_validation_error(self):
        """Тот же человек, тот же день и время — full_clean() даёт ValidationError"""
        Booking.objects.create(customer=self.customer, tour=self.tour, date=TOMORROW, time=TEN_AM)
        duplicate = Booking(customer=self.customer, tour=self.tour2, date=TOMORROW, time=TEN_AM)
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_same_customer_other_time_ok(self):
        """Тот же человек, тот же день, другое время — можно"""
        Booking.objects.create(customer=self.customer, tour=self.tour, date=TOMORROW, time=TEN_AM)
        Booking.objects.create(customer=self.customer, tour=self.tour2, date=TOMORROW, time=TWO_PM)
        self.assertEqual(self.customer.bookings.count(), 2)

    def test_same_customer_other_day_ok(self):
        """Тот же человек, тот же тур и время, другой день — можно"""
        Booking.objects.create(customer=self.customer, tour=self.tour, date=TODAY, time=TEN_AM)
        Booking.objects.create(customer=self.customer, tour=self.tour, date=TOMORROW, time=TEN_AM)
        self.assertEqual(self.customer.bookings.count(), 2)

    def test_other_customer_same_datetime_ok(self):
        """Разные люди могут купить тур на одно и то же время"""
        Booking.objects.create(customer=self.customer, tour=self.tour, date=TOMORROW, time=TEN_AM)
        Booking.objects.create(customer=self.customer2, tour=self.tour, date=TOMORROW, time=TEN_AM)
        self.assertEqual(self.tour.bookings.count(), 2)


# ---------------------------------------------------------------------------
# 3. Комментарии только к турам, в которых был
# ---------------------------------------------------------------------------
class CommentRuleTests(BaseTourTestCase):
    """Несколько комментариев — только к турам, в которых был"""

    def setUp(self):
        super().setUp()
        Booking.objects.create(customer=self.customer, tour=self.tour, date=YESTERDAY, time=TEN_AM)

    def test_several_comments_to_visited_tour(self):
        """Человек может оставить несколько комментариев к туру, где был"""
        for text in ['Отлично', 'Лошади спокойные', 'Поеду ещё']:
            comment = Comment(customer=self.customer, tour=self.tour, text=text, mark=5)
            comment.full_clean()
            comment.save()
        self.assertEqual(self.customer.comments.count(), 3)
        self.assertEqual(self.tour.comments.count(), 3)

    def test_comment_on_not_visited_tour_forbidden(self):
        """Нельзя комментировать тур, который не покупал"""
        comment = Comment(customer=self.customer, tour=self.tour2, text='Не был', mark=1)
        with self.assertRaises(ValidationError):
            comment.full_clean()

    def test_comment_by_other_customer_forbidden(self):
        """Другой человек без покупки не может комментировать"""
        comment = Comment(customer=self.customer2, tour=self.tour, text='Чужой', mark=3)
        with self.assertRaises(ValidationError):
            comment.full_clean()

    def test_comment_on_future_tour_forbidden(self):
        """Нельзя комментировать тур, который ещё не состоялся"""
        Booking.objects.create(customer=self.customer2, tour=self.tour2, date=TOMORROW, time=TEN_AM)
        comment = Comment(customer=self.customer2, tour=self.tour2, text='Рано', mark=4)
        with self.assertRaises(ValidationError):
            comment.full_clean()

    def test_comment_on_today_tour_allowed(self):
        """Тур сегодня — комментировать можно"""
        Booking.objects.create(customer=self.customer2, tour=self.tour2, date=TODAY, time=TEN_AM)
        comment = Comment(customer=self.customer2, tour=self.tour2, text='Сегодня было круто', mark=5)
        comment.full_clean()

    def test_comment_mark_out_of_range(self):
        """Оценка должна быть от 1 до 5"""
        for mark in (0, 6):
            comment = Comment(customer=self.customer, tour=self.tour, text='x', mark=mark)
            with self.assertRaises(ValidationError):
                comment.full_clean()


# ---------------------------------------------------------------------------
# 4. Категории
# ---------------------------------------------------------------------------
class CategoryTests(BaseTourTestCase):
    """Категории тура: конный, пеший, мото"""

    def test_categories_exist(self):
        """Есть категории «конный», «пеший», «мото»"""
        names = set(Category.objects.values_list('name', flat=True))
        self.assertEqual(names, {'конный', 'пеший', 'мото'})

    def test_filter_tours_by_category(self):
        """Фильтрация туров по категории"""
        self.assertEqual(list(Tour.objects.filter(categories__name='мото')), [self.tour2])
        self.assertEqual(list(Tour.objects.filter(categories__name='конный')), [self.tour])

    def test_category_name_unique(self):
        """Название категории уникально"""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(name='конный')


# ---------------------------------------------------------------------------
# 5. Отправка данных (все формы, POST)
# ---------------------------------------------------------------------------
class SubmitDataTests(BaseTourTestCase):
    """Отправка данных через все формы (POST)"""

    def test_all_create_pages_get(self):
        """GET всех форм создания возвращает 200 и шаблон формы"""
        for name in ['create_category', 'create_tour', 'create_route',
                     'create_customer', 'create_booking', 'create_comment']:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
            self.assertTemplateUsed(response, 'tours/form.html')

    # --- Категория ---
    def test_post_category_valid(self):
        """POST категории: валидные данные сохраняются"""
        response = self.client.post(reverse('create_category'), {'name': 'вело'})
        self.assertRedirects(response, reverse('tour_list'))
        self.assertTrue(Category.objects.filter(name='вело').exists())

    def test_post_category_invalid(self):
        """POST категории: пустое и повторяющееся имя не сохраняются"""
        for data in ({'name': ''}, {'name': 'конный'}):
            response = self.client.post(reverse('create_category'), data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].errors)
        self.assertEqual(Category.objects.count(), 3)

    # --- Тур (многие ко многим) ---
    def test_post_tour_valid_with_categories(self):
        """POST тура с несколькими категориями"""
        response = self.client.post(reverse('create_tour'), {
            'title': 'Иссык-Куль: конь + пешком', 'description': 'Берег озера',
            'price': '4500.00', 'duration_hours': 6,
            'categories': [self.horse.id, self.walk.id],
        })
        self.assertRedirects(response, reverse('tour_list'))
        tour = Tour.objects.get(title='Иссык-Куль: конь + пешком')
        self.assertEqual(set(tour.categories.all()), {self.horse, self.walk})

    def test_post_tour_invalid(self):
        """POST тура: без категорий / отрицательная цена / без названия — ошибка"""
        bad = [
            {'title': 'Без категорий', 'price': '100', 'duration_hours': 2},
            {'title': 'Минус', 'price': '-1', 'duration_hours': 2, 'categories': [self.horse.id]},
            {'title': '', 'price': '100', 'duration_hours': 2, 'categories': [self.horse.id]},
            {'title': 'Ноль часов', 'price': '100', 'duration_hours': 0, 'categories': [self.horse.id]},
        ]
        for data in bad:
            response = self.client.post(reverse('create_tour'), data)
            self.assertEqual(response.status_code, 200, data)
            self.assertTrue(response.context['form'].errors)
        self.assertEqual(Tour.objects.count(), 2)

    # --- Маршрут (1 к 1) ---
    def test_post_route_valid(self):
        """POST маршрута для тура"""
        response = self.client.post(reverse('create_route'), {
            'tour': self.tour.id, 'start_point': 'Кочкор',
            'end_point': 'Сон-Куль', 'distance_km': '42.5',
        })
        self.assertRedirects(response, reverse('tour_list'))
        self.assertEqual(self.tour.route.end_point, 'Сон-Куль')

    def test_post_route_second_for_same_tour(self):
        """POST второго маршрута для того же тура — ошибка формы (1 к 1)"""
        TourRoute.objects.create(tour=self.tour, start_point='A', end_point='B', distance_km=1)
        response = self.client.post(reverse('create_route'), {
            'tour': self.tour.id, 'start_point': 'C', 'end_point': 'D', 'distance_km': '5',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('tour', response.context['form'].errors)
        self.assertEqual(TourRoute.objects.count(), 1)

    def test_post_route_invalid_distance(self):
        """POST маршрута с нулевым расстоянием — ошибка"""
        response = self.client.post(reverse('create_route'), {
            'tour': self.tour.id, 'start_point': 'A', 'end_point': 'B', 'distance_km': '0',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('distance_km', response.context['form'].errors)

    # --- Клиент ---
    def test_post_customer_valid(self):
        """POST клиента"""
        response = self.client.post(reverse('create_customer'), {
            'full_name': 'Сидоров Сидор', 'phone': '+996700000003', 'email': 's@mail.kg',
        })
        self.assertRedirects(response, reverse('tour_list'))
        self.assertTrue(Customer.objects.filter(phone='+996700000003').exists())

    def test_post_customer_invalid(self):
        """POST клиента: неверный email и повторный телефон — ошибка"""
        bad = [
            {'full_name': 'X', 'phone': '+996700000009', 'email': 'not-email'},
            {'full_name': 'Y', 'phone': '+996700000001'},
            {'full_name': '', 'phone': '+996700000010'},
        ]
        for data in bad:
            response = self.client.post(reverse('create_customer'), data)
            self.assertEqual(response.status_code, 200, data)
            self.assertTrue(response.context['form'].errors)
        self.assertEqual(Customer.objects.count(), 2)

    # --- Покупка тура ---
    def test_post_booking_valid(self):
        """POST покупки тура"""
        response = self.client.post(reverse('create_booking'), {
            'customer': self.customer.id, 'tour': self.tour.id,
            'date': TOMORROW.isoformat(), 'time': '10:00',
        })
        self.assertRedirects(response, reverse('tour_list'))
        self.assertEqual(self.customer.bookings.count(), 1)

    def test_post_booking_same_datetime_rejected(self):
        """POST второй покупки на тот же день и время — форма отклоняет"""
        Booking.objects.create(customer=self.customer, tour=self.tour, date=TOMORROW, time=TEN_AM)
        response = self.client.post(reverse('create_booking'), {
            'customer': self.customer.id, 'tour': self.tour2.id,
            'date': TOMORROW.isoformat(), 'time': '10:00',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Этот человек уже купил тур на этот день и время.')
        self.assertEqual(self.customer.bookings.count(), 1)

    def test_post_booking_other_time_accepted(self):
        """POST покупки на тот же день, но другое время — принимается"""
        Booking.objects.create(customer=self.customer, tour=self.tour, date=TOMORROW, time=TEN_AM)
        response = self.client.post(reverse('create_booking'), {
            'customer': self.customer.id, 'tour': self.tour2.id,
            'date': TOMORROW.isoformat(), 'time': '14:00',
        })
        self.assertRedirects(response, reverse('tour_list'))
        self.assertEqual(self.customer.bookings.count(), 2)

    def test_post_booking_invalid_data(self):
        """POST покупки: неверная дата, несуществующий тур — ошибка"""
        bad = [
            {'customer': self.customer.id, 'tour': self.tour.id, 'date': '2026-13-40', 'time': '10:00'},
            {'customer': self.customer.id, 'tour': 9999, 'date': TOMORROW.isoformat(), 'time': '10:00'},
            {'customer': self.customer.id, 'tour': self.tour.id, 'date': TOMORROW.isoformat(), 'time': ''},
        ]
        for data in bad:
            response = self.client.post(reverse('create_booking'), data)
            self.assertEqual(response.status_code, 200, data)
            self.assertTrue(response.context['form'].errors)
        self.assertEqual(Booking.objects.count(), 0)

    # --- Комментарий ---
    def test_post_comment_valid_several(self):
        """POST нескольких комментариев к туру, в котором был"""
        Booking.objects.create(customer=self.customer, tour=self.tour, date=YESTERDAY, time=TEN_AM)
        for text in ['Первый', 'Второй']:
            response = self.client.post(reverse('create_comment'), {
                'customer': self.customer.id, 'tour': self.tour.id, 'text': text, 'mark': 5,
            })
            self.assertRedirects(response, reverse('tour_list'))
        self.assertEqual(self.customer.comments.count(), 2)

    def test_post_comment_not_visited_rejected(self):
        """POST комментария к туру, где не был — форма отклоняет"""
        response = self.client.post(reverse('create_comment'), {
            'customer': self.customer.id, 'tour': self.tour2.id, 'text': 'Хочу', 'mark': 4,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Можно комментировать только туры, в которых вы были.')
        self.assertEqual(Comment.objects.count(), 0)

    def test_post_comment_invalid_mark(self):
        """POST комментария с оценкой 10 — ошибка"""
        Booking.objects.create(customer=self.customer, tour=self.tour, date=YESTERDAY, time=TEN_AM)
        response = self.client.post(reverse('create_comment'), {
            'customer': self.customer.id, 'tour': self.tour.id, 'text': 'x', 'mark': 10,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('mark', response.context['form'].errors)
        self.assertEqual(Comment.objects.count(), 0)


# ---------------------------------------------------------------------------
# Страницы просмотра
# ---------------------------------------------------------------------------
class PageViewTests(BaseTourTestCase):
    """Страницы списка и детали тура"""

    def test_tour_list(self):
        """Список туров: 200, шаблон, названия и категории в HTML"""
        response = self.client.get(reverse('tour_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tours/tour_list.html')
        self.assertContains(response, 'Сон-Куль на лошадях')
        self.assertContains(response, 'мото')
        self.assertEqual(list(response.context['tours']), [self.tour2, self.tour])

    def test_tour_detail(self):
        """Деталь тура показывает маршрут, покупки и комментарии"""
        TourRoute.objects.create(tour=self.tour, start_point='Кочкор', end_point='Сон-Куль', distance_km=40)
        Booking.objects.create(customer=self.customer, tour=self.tour, date=YESTERDAY, time=TEN_AM)
        Comment.objects.create(customer=self.customer, tour=self.tour, text='Красота', mark=5)
        response = self.client.get(reverse('tour_detail', args=[self.tour.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Кочкор → Сон-Куль')
        self.assertContains(response, 'Иванов Иван')
        self.assertContains(response, 'Красота')

    def test_tour_detail_404(self):
        """Несуществующий тур — 404"""
        response = self.client.get(reverse('tour_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# 6. Документация (django.contrib.admindocs)
# ---------------------------------------------------------------------------
class DocsTests(BaseTourTestCase):
    """Документация через django admindocs"""

    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser('admin', 'a@a.kg', 'admin12345')

    def test_docs_require_login(self):
        """Без входа документация редиректит на логин"""
        response = self.client.get('/admin/doc/')
        self.assertEqual(response.status_code, 302)

    def test_docs_index_and_models(self):
        """Админ видит главную документации и список моделей"""
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/admin/doc/').status_code, 200)
        response = self.client.get('/admin/doc/models/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Booking')

    def test_docs_model_page_has_docstring(self):
        """Страница модели Booking содержит описание правила"""
        self.client.force_login(self.admin)
        response = self.client.get('/admin/doc/models/tours.booking/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'один человек может купить только один тур')

    def test_docs_views_page(self):
        """Страница документации представлений открывается"""
        self.client.force_login(self.admin)
        response = self.client.get('/admin/doc/views/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'create_booking_view')

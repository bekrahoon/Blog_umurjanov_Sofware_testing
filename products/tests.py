from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from products.forms import ProductForm
from products.models import Product


class ProductModelTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Ноутбук',
            description='Игровой ноутбук',
            price=Decimal('55000.00'),
            quantity=3,
        )

    def test_product_model_creation(self):
        """Модель Product создаётся с нужными полями, __str__ возвращает название"""
        self.assertEqual(self.product.name, 'Ноутбук')
        self.assertEqual(self.product.price, Decimal('55000.00'))
        self.assertEqual(self.product.quantity, 3)
        self.assertEqual(str(self.product), 'Ноутбук')

    def test_product_default_quantity(self):
        """Если quantity не указан, по умолчанию он равен 0"""
        product = Product.objects.create(name='Мышь', price=Decimal('500'))
        self.assertEqual(product.quantity, 0)

    def test_product_dates_filled(self):
        """created_at и updated_at заполняются автоматически"""
        self.assertIsNotNone(self.product.created_at)
        self.assertIsNotNone(self.product.updated_at)


class ProductFormTests(TestCase):
    def test_form_valid(self):
        """Форма с корректными данными валидна"""
        form = ProductForm(data={'name': 'Клавиатура', 'description': '', 'price': '1500', 'quantity': 5})
        self.assertTrue(form.is_valid())

    def test_form_without_name_invalid(self):
        """Форма без названия невалидна (name — обязательное поле)"""
        form = ProductForm(data={'name': '', 'price': '1500', 'quantity': 5})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_form_negative_quantity_invalid(self):
        """Отрицательное количество не проходит валидацию"""
        form = ProductForm(data={'name': 'Монитор', 'price': '9000', 'quantity': -1})
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_form_wrong_price_invalid(self):
        """Цена-текст не проходит валидацию"""
        form = ProductForm(data={'name': 'Монитор', 'price': 'дорого', 'quantity': 1})
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)


class ProductCRUDTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(
            name='Телефон',
            description='Смартфон',
            price=Decimal('20000.00'),
            quantity=10,
        )

    # ---------- READ ----------
    def test_product_list_view(self):
        """READ: список товаров — код 200, нужный шаблон, товар на странице"""
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product_list.html')
        self.assertContains(response, 'Телефон')

    def test_product_list_empty(self):
        """READ: при пустой базе выводится «Товаров пока нет»"""
        Product.objects.all().delete()
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Товаров пока нет')

    def test_product_detail_view(self):
        """READ: страница товара — код 200, название, цена и количество"""
        response = self.client.get(reverse('product_detail', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product_detail.html')
        self.assertContains(response, 'Телефон')
        self.assertContains(response, '20000')
        self.assertContains(response, 'Количество: 10')

    def test_product_detail_404(self):
        """READ: несуществующий товар возвращает 404"""
        response = self.client.get(reverse('product_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)

    # ---------- CREATE ----------
    def test_product_create_get(self):
        """CREATE: GET открывает пустую форму создания"""
        response = self.client.get(reverse('product_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product_form.html')
        self.assertContains(response, 'Новый товар')

    def test_product_create_post(self):
        """CREATE: POST с корректными данными создаёт товар и редиректит на него"""
        response = self.client.post(reverse('product_create'), {
            'name': 'Наушники',
            'description': 'Беспроводные',
            'price': '3500',
            'quantity': 7,
        })
        self.assertEqual(Product.objects.count(), 2)
        new = Product.objects.get(name='Наушники')
        self.assertRedirects(response, reverse('product_detail', args=[new.id]))
        self.assertEqual(new.price, Decimal('3500'))

    def test_product_create_invalid(self):
        """CREATE: POST с пустым названием не создаёт товар, форма показывается снова"""
        response = self.client.post(reverse('product_create'), {
            'name': '',
            'price': '100',
            'quantity': 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 1)
        self.assertTrue(response.context['form'].errors)

    # ---------- UPDATE ----------
    def test_product_update_get(self):
        """UPDATE: GET открывает форму с текущими данными товара"""
        response = self.client.get(reverse('product_update', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Редактировать товар')
        self.assertContains(response, 'value="Телефон"')

    def test_product_update_post(self):
        """UPDATE: POST меняет данные товара и редиректит на его страницу"""
        response = self.client.post(reverse('product_update', args=[self.product.id]), {
            'name': 'Телефон Pro',
            'description': 'Новая модель',
            'price': '25000',
            'quantity': 4,
        })
        self.assertRedirects(response, reverse('product_detail', args=[self.product.id]))
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Телефон Pro')
        self.assertEqual(self.product.price, Decimal('25000'))
        self.assertEqual(self.product.quantity, 4)

    def test_product_update_invalid(self):
        """UPDATE: некорректные данные не сохраняются"""
        response = self.client.post(reverse('product_update', args=[self.product.id]), {
            'name': 'Телефон',
            'price': 'abc',
            'quantity': 4,
        })
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, Decimal('20000.00'))

    def test_product_update_404(self):
        """UPDATE: редактирование несуществующего товара — 404"""
        response = self.client.get(reverse('product_update', args=[9999]))
        self.assertEqual(response.status_code, 404)

    # ---------- DELETE ----------
    def test_product_delete_get_confirm(self):
        """DELETE: GET показывает страницу подтверждения и НЕ удаляет товар"""
        response = self.client.get(reverse('product_delete', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product_confirm_delete.html')
        self.assertTrue(Product.objects.filter(id=self.product.id).exists())

    def test_product_delete_post(self):
        """DELETE: POST удаляет товар и редиректит на список"""
        response = self.client.post(reverse('product_delete', args=[self.product.id]))
        self.assertRedirects(response, reverse('product_list'))
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_product_delete_404(self):
        """DELETE: удаление несуществующего товара — 404"""
        response = self.client.post(reverse('product_delete', args=[9999]))
        self.assertEqual(response.status_code, 404)

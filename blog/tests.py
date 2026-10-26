import re

from django.test import TestCase, Client
from django.urls import reverse
from blog.models import Blog


class BlogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.blog = Blog.objects.create(
            title = 'Тестовый заголовок',
            description = 'Тестовое описание для проверки блога',
            image = 'blog/test_image.jpg',
            author = "Тестовый Автор"
        )
    def test_blog_model_creation(self):
        """Модель Blog создаётся с нужными полями, __str__ возвращает заголовок"""
        self.assertEqual(self.blog.title, 'Тестовый заголовок')
        self.assertEqual(self.blog.author, 'Тестовый Автор')

        self.assertEqual(str(self.blog), 'Тестовый заголовок')

    def test_blog_list_view(self):
        """Список блогов: код 200, шаблон blog_list.html, блог на странице"""
        url = reverse('blog_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'blog_list.html')

        self.assertContains(response, 'Тестовый заголовок')

    def test_blog_detail_not_found(self):
        """Несуществующий id на детальной странице даёт 404"""
        url = reverse('blog_detail', args=[999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_author_display_with_rank(self):
        """У автора по умолчанию (Ivanov Ivan) есть приписка «Главный редактор»"""
        default_blog = Blog.objects.create(
            title = 'Пост Иванова',
            description = 'Текст....',
            image = 'blog/test.jpg'
        )
        url = reverse('blog_detail', args=[default_blog.id])
        response = self.client.get(url)

        self.assertContains(response, "Ivanov Ivan (Главный редактор)")


class BlogListDetailTests(TestCase):
    """Тесты на List и Detail: разные варианты получения данных"""

    def setUp(self):
        self.client = Client()
        self.blog1 = Blog.objects.create(
            title='Первый блог',
            description='Описание первого блога',
            image='blog/one.jpg',
        )
        self.blog2 = Blog.objects.create(
            title='Второй блог',
            description='Описание второго блога',
            image='blog/two.jpg',
            author='Петров Пётр',
        )

    # ---------- List ----------

    def test_list_returns_content(self):
        """1. На выходе получаем контент: все блоги есть на странице и в контексте"""
        response = self.client.get(reverse('blog_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Первый блог')
        self.assertContains(response, 'Второй блог')
        self.assertEqual(len(response.context['blog']), 2)

    def test_list_empty(self):
        """2. Контента нет: страница открывается и пишет, что блогов нет"""
        Blog.objects.all().delete()
        response = self.client.get(reverse('blog_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['blog']), 0)
        self.assertContains(response, 'Блогов пока нет')

    def test_list_order_newest_first(self):
        """3. Новые блоги идут первыми (order_by('-id'))"""
        response = self.client.get(reverse('blog_list'))
        blogs = list(response.context['blog'])
        self.assertEqual(blogs[0], self.blog2)
        self.assertEqual(blogs[1], self.blog1)

    def test_list_links_contain_id(self):
        """4. В ссылках «Подробнее» есть правильный id каждого блога"""
        response = self.client.get(reverse('blog_list'))
        self.assertContains(response, f'href="/blog_list/{self.blog1.id}/"')
        self.assertContains(response, f'href="/blog_list/{self.blog2.id}/"')

    def test_list_links_really_open(self):
        """5. По ссылкам со страницы списка действительно можно перейти"""
        response = self.client.get(reverse('blog_list'))
        links = re.findall(r'href="(/blog_list/\d+/)"', response.content.decode())
        self.assertEqual(len(links), 2)
        for link in links:
            detail = self.client.get(link)
            self.assertEqual(detail.status_code, 200)
            self.assertTemplateUsed(detail, 'blog_detail.html')

    # ---------- Detail ----------

    def test_detail_returns_content(self):
        """6. Detail по существующему id отдаёт нужный блог"""
        response = self.client.get(reverse('blog_detail', args=[self.blog1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog_detail.html')
        self.assertEqual(response.context['blog_id'].id, self.blog1.id)
        self.assertContains(response, 'Описание первого блога')

    def test_detail_shows_correct_blog_only(self):
        """7. На детальной странице только свой блог, чужого нет"""
        response = self.client.get(reverse('blog_detail', args=[self.blog1.id]))
        self.assertContains(response, 'Первый блог')
        self.assertNotContains(response, 'Второй блог')

    def test_detail_without_rank_for_other_author(self):
        """8. У обычного автора нет приписки «Главный редактор»"""
        response = self.client.get(reverse('blog_detail', args=[self.blog2.id]))
        self.assertContains(response, 'Петров Пётр')
        self.assertNotContains(response, '(Главный редактор)')

    def test_detail_after_delete_is_404(self):
        """9. После удаления блога его страница даёт 404"""
        blog_id = self.blog1.id
        self.blog1.delete()
        response = self.client.get(reverse('blog_detail', args=[blog_id]))
        self.assertEqual(response.status_code, 404)

    def test_detail_wrong_id_type_is_404(self):
        """10. Вместо id текст: URL не совпадает, 404"""
        response = self.client.get('/blog_list/abc/')
        self.assertEqual(response.status_code, 404)


class BlogLikesTests(TestCase):
    """Тесты счётчика лайков/просмотров"""

    def setUp(self):
        self.client = Client()
        self.blog = Blog.objects.create(
            title='Блог для лайков',
            description='Текст',
            image='blog/like.jpg',
        )

    def test_new_blog_has_zero_likes(self):
        """У нового блога лайков 0"""
        self.assertEqual(self.blog.likes, 0)

    def test_detail_view_increments_likes(self):
        """GET на детальную страницу увеличивает лайки на 1"""
        self.client.get(reverse('blog_detail', args=[self.blog.id]))
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.likes, 1)

    def test_several_visits(self):
        """3 захода дают 3 лайка"""
        url = reverse('blog_detail', args=[self.blog.id])
        for _ in range(3):
            self.client.get(url)
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.likes, 3)

    def test_list_does_not_change_likes(self):
        """Заход на список лайки не меняет"""
        self.client.get(reverse('blog_list'))
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.likes, 0)

    def test_likes_only_for_opened_blog(self):
        """Лайк добавляется только открытому блогу, другому нет"""
        other = Blog.objects.create(title='Другой', description='...', image='blog/x.jpg')
        self.client.get(reverse('blog_detail', args=[self.blog.id]))
        other.refresh_from_db()
        self.assertEqual(other.likes, 0)

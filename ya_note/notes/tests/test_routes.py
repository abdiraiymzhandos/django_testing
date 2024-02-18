from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note


class YaNoteRouteTests(TestCase):
    def setUp(self):
        # Создание пользователей
        self.author_user = User.objects.create_user(
            username='testuser', password='12345')
        self.reader_user = User.objects.create_user(
            username='otheruser', password='12345')

        # Создание клиентов для имитации сессий пользователей
        self.author_client = Client()
        self.reader_client = Client()

        # Логин пользователей через их клиенты
        self.author_client.force_login(self.author_user)
        self.reader_client.force_login(self.reader_user)

        # Создание заметки автором
        self.note = Note.objects.create(
            title='Test Note',
            text='This is a test note.',
            slug='test-note', author=self.author_user)

    def test_anonymous_user_access(self):
        """Проверяет доступность и редиректы для анонимных пользователей."""
        # Список URL для проверки
        urls_to_test = [
            ('notes:home', 'get'),
            ('notes:login', 'get'),
            ('notes:logout', 'get'),
            ('users:signup', 'get'),
        ]
        for url_name, method in urls_to_test:
            if method == 'get':
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_for_authenticated_user(self):
        """Проверяет доступность страниц для
        аутентифицированных пользователей.
        """
        urls = [
            reverse('notes:list'),
            reverse('notes:add'),
            reverse('notes:success')
        ]
        for client in [self.author_client, self.reader_client]:
            for url in urls:
                with self.subTest(url=url, client=client):
                    response = client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_anonymous_user_to_login(self):
        """
        Проверяет, что анонимный пользователь перенаправляется на страницу
        входа при попытке доступа к защищенным страницам.
        """
        pages = [
            ('notes:list', {}),
            ('notes:success', {}),
            ('notes:add', {}),
            ('notes:detail', {'slug': self.note.slug}),
            ('notes:edit', {'slug': self.note.slug}),
            ('notes:delete', {'slug': self.note.slug}),
        ]

        login_url = reverse('notes:login')
        for view_name, kwargs in pages:
            with self.subTest(view_name=view_name):
                url = reverse(view_name, kwargs=kwargs)
                expected_redirect_url = f"{login_url}?next={url}"
                response = self.client.get(url)
                self.assertRedirects(response, expected_redirect_url)

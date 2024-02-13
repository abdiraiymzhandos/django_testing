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
        response = self.client.get(reverse('notes:home'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        response2 = self.client.get(reverse('notes:list'))
        expected_redirect_url = '/auth/login/?next=/notes/'
        self.assertRedirects(response2, expected_redirect_url)

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

    def test_note_pages_accessibility_by_role(self):
        """
        Проверяет доступность страниц отдельной заметки, удаления и
        редактирования заметки
        в зависимости от роли пользователя (автора или читателя).
        """
        tests = [
            (self.author_client, HTTPStatus.OK, 'notes:detail',
             {'slug': self.note.slug}),
            (self.reader_client, HTTPStatus.NOT_FOUND, 'notes:detail',
             {'slug': self.note.slug}),
            (self.author_client, HTTPStatus.OK, 'notes:edit',
             {'slug': self.note.slug}),
            (self.reader_client, HTTPStatus.NOT_FOUND, 'notes:edit',
             {'slug': self.note.slug}),
            (self.author_client, HTTPStatus.OK, 'notes:delete',
             {'slug': self.note.slug}),
            (self.reader_client, HTTPStatus.NOT_FOUND, 'notes:delete',
             {'slug': self.note.slug}),
        ]

        for client, expected_status, view_name, kwargs in tests:
            with self.subTest(client=client, view_name=view_name):
                url = reverse(view_name, kwargs=kwargs)
                response = client.get(url)
                self.assertEqual(response.status_code, expected_status)

    def test_note_detail_page_for_other_user(self):
        self.client.login(username='otheruser', password='12345')
        response = self.client.get(reverse(
            'notes:detail', kwargs={'slug': self.note.slug}))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_login_page_accessibility(self):
        url = reverse('notes:login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

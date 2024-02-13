from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


class NoteContentTests(TestCase):
    def setUp(self):
        # Создание и логин пользователей
        self.user1 = User.objects.create_user(
            username='user1',
            password='password1')
        self.user2 = User.objects.create_user(
            username='user2',
            password='password2')

        # Создание клиентов для пользователей
        self.client_user1 = self.client
        self.client_user1.login(username='user1', password='password1')

        self.client_user2 = self.client
        self.client_user2.login(username='user2', password='password2')

        # Создание заметок
        self.note1 = Note.objects.create(
            title="User 1's note", text="A note by user 1",
            slug="user1-note", author=self.user1)
        self.note2 = Note.objects.create(
            title="User 2's note", text="A note by user 2",
            slug="user2-note", author=self.user2)

    def test_notes_list_for_different_users(self):
        """Проверка отображения списка заметок для разных пользователей."""
        test_cases = [
            (self.client_user2, self.note2.title, True, self.user2.username),
            (self.client_user2, self.note1.title, False, self.user2.username),
        ]

        for client, note_title, expected, username in test_cases:
            with self.subTest(user=username, note_title=note_title):
                response = client.get(reverse('notes:list'))
                note_titles = [note.title for note in response.context[
                    'object_list']]
                note_exists = note_title in note_titles
                self.assertIs(note_exists, expected)

    def test_form_presence_on_add_and_edit_pages(self):
        """
        Проверка наличия формы для добавления и редактирования заметки
        на соответствующих страницах.
        Убедимся, что при переходе на страницы добавления и редактирования
        заметки в контексте ответа содержится форма NoteForm.
        """
        self.client.login(username='user1', password='password1')

        test_cases = [
            (reverse('notes:add'), None),  # URL для добавления заметки
            (reverse('notes:edit', kwargs={'slug': self.note1.slug}),
             self.note1.slug),  # URL для редактирования заметки
        ]

        for url, slug in test_cases:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)

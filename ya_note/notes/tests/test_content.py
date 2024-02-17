from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


class NoteContentTests(TestCase):
    def setUp(self):
        # Создание и логин пользователей
        self.user1 = User.objects.create_user(username='user1',
                                              password='password1')
        self.user2 = User.objects.create_user(username='user2',
                                              password='password2')

        # Создание заметок
        self.note_user1 = Note.objects.create(title="User 1's note",
                                              text="A note by user 1",
                                              slug="user1-note",
                                              author=self.user1)
        self.note_user2 = Note.objects.create(title="User 2's note",
                                              text="A note by user 2",
                                              slug="user2-note",
                                              author=self.user2)

    def test_note_visibility_per_user(self):
        """Проверка видимости заметок для разных пользователей."""
        self.client.login(username='user1', password='password1')
        response_user1 = self.client.get(reverse('notes:list'))
        notes_user1 = list(response_user1.context['object_list'])
        self.assertNotIn(self.note_user2, notes_user1)

        self.client.login(username='user2', password='password2')
        response_user2 = self.client.get(reverse('notes:list'))
        notes_user2 = list(response_user2.context['object_list'])
        self.assertNotIn(self.note_user1, notes_user2)

    def test_form_presence_on_add_and_edit_pages(self):
        """
        Проверка наличия формы для добавления и редактирования заметки
        на соответствующих страницах.
        Убедимся, что при переходе на страницы добавления и редактирования
        заметки в контексте ответа содержится форма NoteForm.
        """
        self.note = Note.objects.create(
            title="User 3's note", text="A note by user 3",
            slug="user3-note", author=self.user1)
        self.client.login(username='user1', password='password1')

        test_cases = [
            (reverse('notes:add'), None),  # URL для добавления заметки
            (reverse('notes:edit', kwargs={'slug': self.note.slug}),
             self.note.slug),  # URL для редактирования заметки
        ]

        for url, slug in test_cases:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)

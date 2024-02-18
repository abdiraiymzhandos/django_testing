from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


class NoteContentTests(TestCase):
    def setUp(self):
        # Create and log in users
        self.user1 = User.objects.create_user(username='user1',
                                              password='password1')
        self.user2 = User.objects.create_user(username='user2',
                                              password='password2')

        # Log in clients for author and reader
        self.author_client = self.client
        self.reader_client = self.client
        self.author_client.login(username='user1', password='password1')
        self.reader_client.login(username='user2', password='password2')

        # Create notes
        self.note_user1 = Note.objects.create(title="User 1's note",
                                              text="A note by user 1",
                                              slug="user1-note",
                                              author=self.user1)

    def test_note_visibility_per_user(self):
        """Test note visibility for different users."""
        test_cases = [
            (self.author_client, False),
            (self.reader_client, False),
        ]

        for client, expected in test_cases:
            with self.subTest(client=client):
                response = client.get(reverse('notes:list'))
                notes_in_list = list(response.context['object_list'])
                self.assertIs(self.note_user1 in notes_in_list, expected)

    def test_form_presence_on_add_and_edit_pages(self):
        """
        Проверка наличия формы для добавления и редактирования заметки
        на соответствующих страницах.
        Убедимся, что при переходе на страницы добавления и редактирования
        заметки в контексте ответа содержится форма NoteForm.
        """
        self.client.login(username='user1', password='password1')

        test_cases = [
            reverse('notes:add'),
            reverse('notes:edit', kwargs={'slug': self.note_user1.slug}),
        ]

        for url in test_cases:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)

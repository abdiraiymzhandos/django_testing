from django.urls import reverse
from django.test import TestCase
from django.contrib.auth.models import User
from notes.models import Note
from notes.forms import NoteForm


class NoteContentTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1', password='password1')
        self.user2 = User.objects.create_user(
            username='user2', password='password2')

        Note.objects.create(title="User 1's note", text="A note by user 1",
                            slug="user1-note", author=self.user1)
        Note.objects.create(title="User 2's note", text="A note by user 2",
                            slug="user2-note", author=self.user2)

    def test_notes_list_for_different_users(self):
        self.client.login(username='user1', password='password1')
        response = self.client.get(reverse('notes:list'))
        self.assertContains(response, "User 1's note", html=True)

    def test_add_page_contains_note_form(self):
        self.client.login(username='user1', password='password1')
        response = self.client.get(reverse('notes:add'))
        self.assertIsInstance(response.context['form'], NoteForm)

    def test_edit_page_contains_note_form(self):
        self.client.login(username='user1', password='password1')
        response = self.client.get(reverse(
            'notes:edit', kwargs={'slug': 'user1-note'}))
        self.assertIsInstance(response.context['form'], NoteForm)

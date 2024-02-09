from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from notes.models import Note


class YaNoteRouteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='12345')
        self.other_user = User.objects.create_user(
            username='otheruser', password='12345')
        self.note = Note.objects.create(
            title='Test Note',
            text='This is a test note.',
            slug='test-note', author=self.user)

    def test_home_page_for_anonymous_user(self):
        response = self.client.get(reverse('notes:home'))
        self.assertEqual(response.status_code, 200)

    def test_notes_list_page_for_authenticated_user(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('notes:list'))
        self.assertEqual(response.status_code, 200)

    def test_notes_list_page_redirects_anonymous_user(self):
        response = self.client.get(reverse('notes:list'))
        self.assertRedirects(response, '/auth/login/?next=/notes/')

    def test_note_detail_page_for_author(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse(
            'notes:detail', kwargs={'slug': self.note.slug}))
        self.assertEqual(response.status_code, 200)

    def test_note_detail_page_for_other_user(self):
        self.client.login(username='otheruser', password='12345')
        response = self.client.get(reverse(
            'notes:detail', kwargs={'slug': self.note.slug}))
        self.assertEqual(response.status_code, 404)

    def test_notes_add_page_for_authenticated_user(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('notes:add'))
        self.assertEqual(response.status_code, 200)

    def test_notes_done_page_for_authenticated_user(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('notes:success'))
        self.assertEqual(response.status_code, 200)

    def test_note_edit_page_for_non_author(self):
        self.client.login(username='otheruser', password='12345')
        response = self.client.get(reverse(
            'notes:edit', kwargs={'slug': self.note.slug}))
        self.assertEqual(response.status_code, 404)

    def test_note_delete_page_for_non_author(self):
        self.client.login(username='otheruser', password='12345')
        response = self.client.get(reverse(
            'notes:delete', kwargs={'slug': self.note.slug}))
        self.assertEqual(response.status_code, 404)

    def test_login_page_accessibility(self):
        response = self.client.get('/auth/login/')
        self.assertEqual(response.status_code, 200)

from django.test import TestCase
from django.contrib.auth.models import User
from notes.models import Note
from pytils.translit import slugify
from django.urls import reverse


class NoteLogicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='user', email='user@example.com', password='password')
        self.other_user = User.objects.create_user(
            username='other_user',
            email='other_user@example.com',
            password='password')
        self.note = Note.objects.create(
            title="Test Note",
            text="This is a test note.",
            slug="test-note", author=self.user)

    def test_user_can_create_note(self):
        self.client.login(username='user', password='password')
        response = self.client.post(reverse('notes:add'),
                                    {'title': 'New Note',
                                     'text': 'A new note.',
                                     'slug': 'new-note'})
        self.assertEqual(Note.objects.filter(slug='new-note').count(), 1)

    def test_anonymous_user_cant_create_note(self):
        response = self.client.post(reverse('notes:add'),
                                    {'title': 'New Note',
                                     'text': 'A new note.',
                                     'slug': 'new-note-anon'})
        self.assertEqual(Note.objects.filter(slug='new-note-anon').count(), 0)

    def test_not_unique_slug(self):
        self.client.login(username='user', password='password')
        response = self.client.post(reverse('notes:add'),
                                    {'title': 'Another Note',
                                     'text': 'Another note.',
                                     'slug': 'test-note'})
        self.assertEqual(Note.objects.filter(slug='test-note').count(), 1)

    def test_empty_slug(self):
        self.client.login(username='user', password='password')
        response = self.client.post(reverse('notes:add'),
                                    {'title': 'Unique Note',
                                     'text': 'A unique note.',
                                     'slug': ''})
        generated_slug = slugify('Unique Note')
        self.assertEqual(Note.objects.filter(slug=generated_slug).count(), 1)

    def test_author_can_edit_note(self):
        self.client.login(username='user', password='password')
        edit_url = reverse('notes:edit', kwargs={'slug': self.note.slug})
        response = self.client.post(edit_url,
                                    {'title': 'Edited Note',
                                     'text': 'Edited text.',
                                     'slug': 'edited-note'})
        self.assertTrue(Note.objects.filter(slug='edited-note').exists())

    def test_other_user_cant_edit_note(self):
        self.client.login(username='other_user', password='password')
        edit_url = reverse('notes:edit', kwargs={'slug': self.note.slug})
        response = self.client.post(edit_url,
                                    {'title': 'Malicious Edit',
                                     'text': 'Attempted edit.',
                                     'slug': 'malicious-edit'})
        self.assertFalse(Note.objects.filter(title='Malicious Edit').exists())

    def test_author_can_delete_note(self):
        self.client.login(username='user', password='password')
        delete_url = reverse('notes:delete', kwargs={'slug': self.note.slug})
        response = self.client.post(delete_url)
        self.assertFalse(Note.objects.filter(slug='test-note').exists())

    def test_other_user_cant_delete_note(self):
        self.client.login(username='other_user', password='password')
        delete_url = reverse('notes:delete', kwargs={'slug': self.note.slug})
        response = self.client.post(delete_url)
        self.assertTrue(Note.objects.filter(slug='test-note').exists())

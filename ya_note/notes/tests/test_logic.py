from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

from pytils.translit import slugify

TEST_TITLE = 'Test Title'
TEST_TEXT = 'Test Text'
TEST_SLUG = 'test-slug'
EXISTING_TITLE = 'Existing Title'
EXISTING_TEXT = 'Existing Text'
EXISTING_SLUG = 'existing-slug'


class NoteTestCase(TestCase):
    """
    Класс для тестирования функциональности заметок.

    Описывает тесты для создания, редактирования и удаления заметок.
    Проверяет, что пользователи могут создавать заметки, редактировать и
    удалять свои заметки,
    а также проверяет ограничения для анонимных пользователей и пользователей,
    не являющихся авторами заметок.
    """
    def setUp(self):
        """
        Подготавливает данные для тестирования.

        Создает пользователей (автора и не автора заметок),
        клиенты для имитации авторизованных сессий,
        начальные данные для формы создания заметки и заметку,
        принадлежащую автору.
        """
        self.author = User.objects.create_user(
            username='author', password='password')
        self.not_author = User.objects.create_user(
            username='not_author', password='password')
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)
        self.form_data = {
            'title': TEST_TITLE,
            'text': TEST_TEXT,
            'slug': TEST_SLUG
        }
        self.note = Note.objects.create(
            title=EXISTING_TITLE,
            text=EXISTING_TEXT,
            slug=EXISTING_SLUG,
            author=self.author
        )

    def test_user_can_create_note(self):
        """
        Тест на возможность пользователя создать заметку.

        Проверяет, что авторизованный пользователь может успешно
        создать заметку и
        что после создания количество заметок в базе данных увеличивается.
        """
        Note.objects.all().delete()
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.latest('id')
        self.assertEqual(new_note.title, TEST_TITLE)
        self.assertEqual(new_note.text, TEST_TEXT)
        self.assertEqual(new_note.slug, TEST_SLUG)
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """
        Тест на невозможность анонимного пользователя создать заметку.

        Проверяет, что анонимный пользователь перенаправляется на страницу
        входа при попытке создать заметку.
        """
        url = reverse('notes:add')
        response = self.client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 1)

    def test_not_unique_slug(self):
        """
        Тест на проверку уникальности slug заметки.

        Проверяет, что система не позволяет создать заметку с slug,
        который уже существует в базе данных.
        """
        url = reverse('notes:add')
        self.form_data['slug'] = EXISTING_SLUG
        response = self.author_client.post(url, data=self.form_data)
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note.slug + WARNING))
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """
        Тест на создание заметки без явного указания slug.

        Проверяет, что при отсутствии slug в форме создания заметки,
        slug генерируется автоматически из заголовка.
        """
        Note.objects.all().delete()
        url = reverse('notes:add')
        self.form_data.pop('slug')
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.latest('id')
        expected_slug = slugify(TEST_TITLE)
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """
        Тест на возможность автора редактировать свою заметку.

        Проверяет, что автор заметки может успешно изменить заголовок,
        текст и slug заметки.
        """
        url = reverse('notes:edit', args=(EXISTING_SLUG,))
        response = self.author_client.post(url, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, TEST_TITLE)
        self.assertEqual(self.note.text, TEST_TEXT)
        self.assertEqual(self.note.slug, TEST_SLUG)

    def test_other_user_cant_edit_note(self):
        """
        Тест на невозможность редактирования заметки пользователем,
        не являющимся автором.

        Проверяет, что пользователь, не являющийся автором заметки,
        не может редактировать заметку и получает ошибку 404.
        """
        url = reverse('notes:edit', args=(EXISTING_SLUG,))
        response = self.not_author_client.post(url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, EXISTING_TITLE)
        self.assertEqual(self.note.text, EXISTING_TEXT)
        self.assertEqual(self.note.slug, EXISTING_SLUG)

    def test_author_can_delete_note(self):
        """
        Тест на возможность автора удалить свою заметку.

        Проверяет, что автор заметки может успешно удалить свою заметку и
        после удаления заметка исчезает из базы данных.
        """
        url = reverse('notes:delete', args=(EXISTING_SLUG,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        """
        Тест на невозможность удаления заметки пользователем,
        не являющимся автором.

        Проверяет, что пользователь, не являющийся автором заметки,
        не может удалить заметку и получает ошибку 404.
        """
        url = reverse('notes:delete', args=(EXISTING_SLUG,))
        response = self.not_author_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)

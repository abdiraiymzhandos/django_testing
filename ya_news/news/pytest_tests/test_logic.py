# Import the correct Client class from django.test
from django.test import Client
import pytest
from django.contrib.auth import get_user_model
from http import HTTPStatus
from news.models import News, Comment
from django.urls import reverse
from news.forms import BAD_WORDS, WARNING


User = get_user_model()


@pytest.fixture
def user_and_client(db):
    # Use the correct Django model for creating a user
    user = User.objects.create_user(
        username='Мимо Крокодил', password='password')
    # Instantiate the Client directly from django.test
    client = Client()
    client.force_login(user)
    return user, client


@pytest.fixture
def news_item(db):
    return News.objects.create(title='Заголовок', text='Текст')


@pytest.fixture
def comment(db, user_and_client, news_item):
    user, _ = user_and_client
    return Comment.objects.create(
        news=news_item, author=user, text='Текст комментария')


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, news_item):
    url = reverse('news:detail', args=(news_item.id,))
    form_data = {'text': 'Текст комментария'}
    client.post(url, data=form_data)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_can_create_comment(user_and_client, news_item):
    _, auth_client = user_and_client
    url = reverse('news:detail', args=(news_item.id,))
    form_data = {'text': 'Текст комментария'}
    response = auth_client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert Comment.objects.count() == 1
    comment = Comment.objects.first()
    assert comment.text == 'Текст комментария'


@pytest.mark.django_db
def test_user_cant_use_bad_words(user_and_client, news_item):
    _, auth_client = user_and_client
    url = reverse('news:detail', args=(news_item.id,))
    form_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = auth_client.post(url, data=form_data)
    assert WARNING in response.context['form'].errors['text']
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_author_can_edit_and_delete_comment(user_and_client, comment):
    user, auth_client = user_and_client
    edit_url = reverse('news:edit', args=(comment.id,))
    delete_url = reverse('news:delete', args=(comment.id,))
    new_text = 'Обновленный текст комментария'

    response = auth_client.post(edit_url, {'text': new_text})
    assert response.status_code == HTTPStatus.FOUND
    comment.refresh_from_db()
    assert comment.text == new_text

    response = auth_client.delete(delete_url)
    assert response.status_code == HTTPStatus.FOUND
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_cannot_edit_or_delete_others_comment(user_and_client,
                                                   db, django_user_model,
                                                   news_item):
    other_user = django_user_model.objects.create_user(
        username='Другой пользователь', password='password')
    other_client = Client()
    other_client.force_login(other_user)

    _, comment_owner_client = user_and_client
    comment = Comment.objects.create(
        news=news_item, author=other_user, text='Чужой комментарий')
    edit_url = reverse('news:edit', args=(comment.id,))
    delete_url = reverse('news:delete', args=(comment.id,))

    response = comment_owner_client.post(
        edit_url, {'text': 'Попытка изменения'})
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = comment_owner_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.filter(id=comment.id).exists()

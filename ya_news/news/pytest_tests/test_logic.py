from http import HTTPStatus

import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment

from pytest_django.asserts import assertFormError, assertRedirects

User = get_user_model()


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, news_item):
    url = reverse('news:detail', args=(news_item.id,))
    form_data = {'text': 'Текст комментария'}
    client.post(url, data=form_data)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_can_create_comment(user_and_client, news_item):
    user, auth_client = user_and_client
    url = reverse('news:detail', args=(news_item.id,))
    form_data = {'text': 'Текст комментария'}
    response = auth_client.post(url, data=form_data)
    expected_url = reverse('news:detail', args=(news_item.id,)) + '#comments'

    assertRedirects(response, expected_url, status_code=HTTPStatus.FOUND,
                    target_status_code=HTTPStatus.OK)
    assert Comment.objects.count() == 1
    comment = Comment.objects.first()
    assert comment.text == form_data['text']
    assert comment.news == news_item
    assert comment.author == user


@pytest.mark.django_db
def test_user_cant_use_bad_words(user_and_client, news_item):
    _, auth_client = user_and_client
    url = reverse('news:detail', args=(news_item.id,))
    form_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = auth_client.post(url, data=form_data)
    assertFormError(response, 'form', 'text', WARNING)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_author_can_edit_comment(user_and_client, comment):
    user, auth_client = user_and_client
    edit_url = reverse('news:edit', args=(comment.id,))
    NEW_TEXT = 'Обновленный текст комментария'
    response = auth_client.post(edit_url, {'text': NEW_TEXT})
    assert response.status_code == HTTPStatus.FOUND
    comment.refresh_from_db()
    assert comment.text == NEW_TEXT


@pytest.mark.django_db
def test_author_can_delete_comment(user_and_client, comment):
    user, auth_client = user_and_client
    delete_url = reverse('news:delete', args=(comment.id,))
    response = auth_client.delete(delete_url)
    assert response.status_code == HTTPStatus.FOUND
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_cannot_edit_others_comment(other_user_and_client, test_comments):
    other_user, other_client = other_user_and_client
    comment = test_comments[0]
    original_text = comment.text
    edit_url = reverse('news:edit', args=(comment.id,))
    new_text = 'Попытка изменения'
    response = other_client.post(edit_url, {'text': new_text})
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == original_text


@pytest.mark.django_db
def test_user_cannot_delete_others_comment(admin_client, django_user_model,
                                           news_item):
    other_user = django_user_model.objects.create_user(
        username='Другой пользователь', password='password')
    original_comment_text = 'Чужой комментарий'
    comment = Comment.objects.create(news=news_item, author=other_user,
                                     text=original_comment_text)
    delete_url = reverse('news:delete', args=(comment.id,))
    response = admin_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.filter(id=comment.id).exists()
    comment_after_attempt = Comment.objects.get(id=comment.id)
    # Проверка, что все поля комментария не изменились
    assert comment_after_attempt.news == news_item
    assert comment_after_attempt.author == other_user
    assert comment_after_attempt.text == original_comment_text

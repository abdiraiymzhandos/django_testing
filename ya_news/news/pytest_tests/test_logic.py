from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment

from pytest_django.asserts import assertFormError, assertRedirects

User = get_user_model()


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, test_news):
    url = reverse('news:detail', args=(test_news.id,))
    form_data = {'text': 'Текст комментария'}
    client.post(url, data=form_data)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_can_create_comment(user_and_client, test_news):
    user, auth_client = user_and_client
    url = reverse('news:detail', args=(test_news.id,))
    form_data = {'text': 'Текст комментария'}
    response = auth_client.post(url, data=form_data)
    expected_url = reverse('news:detail', args=(test_news.id,)) + '#comments'

    assertRedirects(response, expected_url, status_code=HTTPStatus.FOUND,
                    target_status_code=HTTPStatus.OK)
    assert Comment.objects.count() == 1
    comment = Comment.objects.first()
    assert comment.text == form_data['text']
    assert comment.news == test_news
    assert comment.author == user


@pytest.mark.django_db
def test_user_cant_use_bad_words(user_and_client, test_news):
    _, auth_client = user_and_client
    url = reverse('news:detail', args=(test_news.id,))
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
def test_user_cannot_edit_others_comment(admin_client, test_comments):
    comment = test_comments[0]
    original_text = comment.text
    edit_url = reverse('news:edit', args=(comment.id,))
    response = admin_client.post(edit_url, {'text': 'Попытка изменения'})
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == original_text


@pytest.mark.django_db
def test_user_cannot_delete_other_users_comment(other_user_and_client,
                                                comment1):
    """
    Проверяем, что пользователь не может удалить комментарий другого
    пользователя. Используем комментарий, созданный в фикстуре comment1.
    """
    response = other_user_and_client.post(reverse('news:delete',
                                                  args=[comment1.pk]))
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_after_attempt = Comment.objects.get(id=comment1.id)
    assert comment_after_attempt.text == comment1.text
    assert comment_after_attempt.author == comment1.author
    assert comment_after_attempt.news == comment1.news

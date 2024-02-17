from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects


@pytest.mark.django_db
def test_pages_availability(client, news):
    urls = [
        ('news:home', None),
        ('news:detail', (news.id,)),
        ('users:login', None),
        ('users:logout', None),
        ('users:signup', None),
    ]
    for name, args in urls:
        url = reverse(name, args=args)
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_comment_author_can_access_edit_and_delete_pages(admin_client,
                                                         comment1):
    """Тест, что автор комментария может получить доступ
    к страницам редактирования и удаления.
    """
    edit_url = reverse('news:edit', args=[comment1.pk])
    delete_url = reverse('news:delete', args=[comment1.pk])

    response = admin_client.get(edit_url)
    assert response.status_code == 200

    response = admin_client.get(delete_url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_non_author_cannot_access_edit_and_delete_pages(other_user_and_client,
                                                        comment1):
    """Тест, что не автор комментария не может получить доступ
    к страницам редактирования и удаления.
    """
    edit_url = reverse('news:edit', args=[comment1.pk])
    delete_url = reverse('news:delete', args=[comment1.pk])

    response = other_user_and_client.get(edit_url)
    assert response.status_code == 404

    response = other_user_and_client.get(delete_url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_redirect_for_anonymous_client(client, comment1):
    login_url = reverse('users:login')
    for name in ('news:edit', 'news:delete'):
        url = reverse(name, args=(comment1.id,))
        redirect_url = f'{login_url}?next={url}'
        response = client.get(url)
        assertRedirects(response, redirect_url)

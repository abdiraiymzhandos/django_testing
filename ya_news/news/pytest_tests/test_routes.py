from http import HTTPStatus

import pytest
from django.urls import reverse
from news.models import Comment, News
from pytest_django.asserts import assertRedirects


@pytest.fixture
def news(db):
    return News.objects.create(title='Заголовок', text='Текст')


@pytest.fixture
def comment(db, news, admin_user):
    return Comment.objects.create(
        news=news,
        author=admin_user,
        text='Текст комментария'
    )


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
@pytest.mark.parametrize('url_name', ['news:edit', 'news:delete'])
def test_availability_for_comment_edit_and_delete(admin_client,
                                                  comment, url_name):
    url = reverse(url_name, args=(comment.id,))
    response = admin_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_redirect_for_anonymous_client(client, comment):
    login_url = reverse('users:login')
    for name in ('news:edit', 'news:delete'):
        url = reverse(name, args=(comment.id,))
        redirect_url = f'{login_url}?next={url}'
        response = client.get(url)
        assertRedirects(response, redirect_url)

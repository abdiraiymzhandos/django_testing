import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from http import HTTPStatus

from news.models import News, Comment

User = get_user_model()


@pytest.fixture
def users(db):
    author = User.objects.create(username='Лев Толстой')
    reader = User.objects.create(username='Читатель простой')
    return {'author': author, 'reader': reader}


@pytest.fixture
def news(db):
    return News.objects.create(title='Заголовок', text='Текст')


@pytest.fixture
def comment(db, users, news):
    return Comment.objects.create(
        news=news,
        author=users['author'],
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
        url = reverse(name, args=args if args else [])
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_availability_for_comment_edit_and_delete(client, users, comment):
    user_status_pairs = [
        (users['author'], HTTPStatus.OK),
        (users['reader'], HTTPStatus.NOT_FOUND),
    ]
    for user, status in user_status_pairs:
        client.force_login(user)
        for name in ('news:edit', 'news:delete'):
            url = reverse(name, args=(comment.id,))
            response = client.get(url)
            assert response.status_code == status
        client.logout()


@pytest.mark.django_db
def test_redirect_for_anonymous_client(client, comment):
    login_url = reverse('users:login')
    for name in ('news:edit', 'news:delete'):
        url = reverse(name, args=(comment.id,))
        redirect_url = f'{login_url}?next={url}'
        response = client.get(url)
        assert response.status_code == HTTPStatus.FOUND
        assert response['Location'] == redirect_url

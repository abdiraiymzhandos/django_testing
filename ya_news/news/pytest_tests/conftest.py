from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone

from news.models import Comment, News

User = get_user_model()


@pytest.fixture
def news(db):
    return News.objects.create(title='Заголовок', text='Текст')


@pytest.fixture
def comment1(db, news, admin_user):
    return Comment.objects.create(
        news=news,
        author=admin_user,
        text='Текст комментария'
    )


@pytest.fixture
def news_items(db):
    today = timezone.now().date()
    all_news = [
        News(
            title=f'News {index}',
            text='Just some text.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    News.objects.bulk_create(all_news)


@pytest.fixture
def test_user(db):
    return User.objects.create(username='Commenter')


@pytest.fixture
def other_user_and_client(db, test_user):
    other_client = Client()
    other_client.force_login(test_user)
    return other_client


@pytest.fixture
def test_news(db):
    return News.objects.create(title='Test News', text='Just some text.')


@pytest.fixture
def test_comments(db, test_news, test_user):
    now = timezone.now()
    comments = []
    for index in range(10):
        comment = Comment(news=test_news, author=test_user,
                          text=f'Comment {index}',
                          created=now + timedelta(days=index))
        comment.save()
        comments.append(comment)
    return comments

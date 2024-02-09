import pytest
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

from news.models import News, Comment
from news.forms import CommentForm

User = get_user_model()


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
    return all_news


@pytest.fixture
def detail_page_setup(db):
    news = News.objects.create(title='Test News', text='Just some text.')
    author = User.objects.create(username='Commenter')
    now = timezone.now()
    comments = [
        Comment(news=news, author=author, text=f'Comment {index}')
        for index in range(10)
    ]
    for index, comment in enumerate(comments):
        comment.created = now + timedelta(days=index)
        comment.save()
    return news, author


@pytest.mark.django_db
def test_news_count_on_home_page(client, news_items):
    response = client.get(reverse('news:home'))
    object_list = response.context['object_list']
    assert len(object_list) == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order_on_home_page(client, news_items):
    response = client.get(reverse('news:home'))
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order_on_detail_page(client, detail_page_setup):
    news, _ = detail_page_setup
    response = client.get(reverse('news:detail', args=[news.id]))
    news = response.context['news']
    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db
def test_form_availability_for_anonymous_client(client, detail_page_setup):
    news, _ = detail_page_setup
    response = client.get(reverse('news:detail', args=[news.id]))
    assert 'form' not in response.context


@pytest.mark.django_db
def test_form_availability_for_authorized_client(client, detail_page_setup):
    news, author = detail_page_setup
    client.force_login(author)
    response = client.get(reverse('news:detail', args=[news.id]))
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)

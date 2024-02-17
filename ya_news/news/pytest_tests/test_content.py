import pytest

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from news.forms import CommentForm

User = get_user_model()


@pytest.mark.django_db
def test_news_count_on_home_page(client, news_items):
    """Тест проверки количества новостей на домашней странице."""
    response = client.get(reverse('news:home'))
    object_list = response.context.get('object_list')
    assert len(object_list) == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order_on_home_page(client, news_items):
    """Тест проверки порядка отображения новостей на домашней странице."""
    response = client.get(reverse('news:home'))
    object_list = response.context.get('object_list')
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order_on_detail_page(client, test_news, test_comments):
    """Тест проверки порядка отображения комментариев
    на странице деталей новости.
    """
    response = client.get(reverse('news:detail', args=[test_news.id]))
    news = response.context.get('news')
    all_comments = news.comment_set.all().order_by('created')
    all_comments_ids = [comment.id for comment in all_comments]
    expected_comments_ids = [comment.id for comment in test_comments]

    assert all_comments_ids == expected_comments_ids


@pytest.mark.django_db
def test_form_availability_for_anonymous_client(client, test_news):
    """Тест проверки доступности формы комментариев для анонимного клиента."""
    response = client.get(reverse('news:detail', args=[test_news.id]))
    assert 'form' not in response.context


@pytest.mark.django_db
def test_form_availability_for_authorized_client(admin_client, test_news):
    """Тест проверки доступности формы комментариев
    для авторизованного клиента.
    """
    response = admin_client.get(reverse('news:detail', args=[test_news.id]))
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)

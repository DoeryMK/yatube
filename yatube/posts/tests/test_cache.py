from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, User


class TestCachPost(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HaHaHa')

    def setUp(self):
        self.client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cach_works_correctly(self):
        """Проверка корректной работы кеширования страницы."""
        cache.clear()
        another_post = Post.objects.create(
            author=self.user,
            text='Еще один новый пост',
        )
        response_1 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(
            response_1.context['page_obj'][0].text, another_post.text
        )
        post = Post.objects.create(
            author=self.user,
            text='Новый пост',
        )
        another_post.delete()
        response_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(
            response_1.content, response_2.content
        )
        self.assertNotEqual(
            response_1.context['page_obj'][0].text, post.text
        )
        cache.clear()
        response_3 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(
            response_3.context['page_obj'][0].text, post.text
        )

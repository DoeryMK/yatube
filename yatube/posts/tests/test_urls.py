from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HaHaHa')
        cls.another_user = User.objects.create_user(username='Alice')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст'
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='group-slug'
        )
        cls.another_post = Post.objects.create(
            author=cls.another_user,
            text='Еще один новый пост'
        )
        cls.urls_guest = {
            reverse(
                'posts:index'):
            'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}):
            'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': cls.post.author}):
            'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.id}):
            'posts/post_detail.html',
        }
        cls.urls_auth = {
            reverse(
                'posts:post_create'):
            'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': cls.post.id}):
            'posts/create_post.html',
            reverse(
                'posts:follow_index'):
            'posts/follow.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.another_user)

    def test_urls_guest_uses_correct_template(self):
        """URL-адреса используют соответствующий шаблон."""
        cache.clear()
        for url, expected_template in PostsURLTests.urls_guest.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, expected_template)

    def test_urls_auth_uses_correct_template(self):
        """URL-адреса использует соответствующий шаблон."""
        for url, expected_template in PostsURLTests.urls_auth.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, expected_template)

    def test_urls_guest_exists_at_desired_location(self):
        """Страницы доступны в соответствии с уровнем доступа
            пользователя "Гость"."""
        for url in PostsURLTests.urls_guest:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_auth_exists_at_desired_location(self):
        """Страницы доступны в соответствии с уровнем доступа
            пользователя "Зарегестрированный пользователь"."""
        for url in PostsURLTests.urls_auth:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                expected_redirect = reverse('users:login') + "?next=" + url
                self.assertRedirects(response, expected_redirect)
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edite_url_exists_at_desired_location(self):
        """Страница /posts/<slug>/edit/ доступна только автору поста."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.another_post.id}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_url(self):
        """Страница /unexisting_page/ вернет ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

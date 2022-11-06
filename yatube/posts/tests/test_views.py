import math
import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from yatube.settings import QUANTITY
from posts.models import Comment, Follow, Group, Post, User


POSTS_QUANTITY = 25

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HaHaHa')
        cls.follower = User.objects.create_user(username='Alice')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='group-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=SimpleUploadedFile(
                name='small.gif',
                content=small_gif,
                content_type='image/gif'
            )
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый комментарий',
            author=cls.user,
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.follower
        )
        for post in range(POSTS_QUANTITY):
            cls.post_newest = Post.objects.create(
                author=cls.user,
                text='Еще один очередной новый текст',
                group=cls.group,
                image=SimpleUploadedFile(
                    name='big.gif',
                    content=small_gif,
                    content_type='image/gif'
                )
            )
        posts_count = Post.objects.all().count()
        cls.pages_amount = math.ceil(posts_count / QUANTITY)
        cls.posts_amount_of_last_page = posts_count % QUANTITY
        cls.url = (
            (reverse(
                'posts:index'), [
                    'page_obj', ], False,),
            (reverse(
                'posts:group_list',
                kwargs={'slug': cls.post_newest.group.slug}), [
                    'page_obj', 'group', ], False,),
            (reverse(
                'posts:profile',
                kwargs={'username': cls.post_newest.author}), [
                    'page_obj', 'author', 'following', ], False,),
            (reverse(
                'posts:post_detail', kwargs={'post_id': cls.post_newest.id}), [
                'post', 'form', 'comments', ], True,),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.follower)

    def data_for_test_of_context(self, response, single_page=False):
        if single_page:
            data = response.context['post']
        else:
            data = response.context['page_obj'][0]
        self.assertEqual(data.text, self.post_newest.text)
        self.assertEqual(data.author, self.post_newest.author)
        self.assertEqual(data.group, self.post_newest.group)
        self.assertIsNotNone(data.image)

    def test_pages_uses_correct_template(self):
        """Views-функция использует соответствующий шаблон."""
        cache.clear()
        templates_page_names = {
            reverse(
                'posts:index'):
            'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.post.author}):
            'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse(
                'posts:post_create'):
            'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
            reverse(
                'posts:follow_index'):
            'posts/follow.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_with_form_show_correct_context(self):
        """Шaблон создания/редактирования поста
            сформирован с правильным контекстом."""
        reverse_pages = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for path in reverse_pages:
            response = self.authorized_client.get(path)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_detail_page_show_correct_context(self):
        """Проверка содержимого контекста страницы.
            Шаблон post_detail сформирован с правильным контекстом
            для комментария."""
        cache.clear()
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertIn('comments', response.context)
        self.assertEqual(response.context['comments'][0].text,
                         self.comment.text)
        self.assertEqual(response.context['comments'][0].post.id,
                         self.post.id)

    def test_pages_context_has_image(self):
        """При выводе поста с картинкой она передается в контекст на страницы
            главная, страницы группы, страница автора."""
        cache.clear()
        reverse_pages = {
            reverse(
                'posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.post.group.slug}),
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author}),
        }
        for reverse_name in reverse_pages:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_obj = response.context['page_obj'][0]
                self.assertIsNotNone(first_obj.image)

    def test_auth_page_show_correct_context(self):
        """Проверка содержимого контекста страницы.
            Шаблоны index, group_list, post_profile, post_detail
            сформированы с правильным контекстом."""
        cache.clear()
        for reverse_name, values, single_page in self.url:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                for expected in values:
                    with self.subTest(expected=expected):
                        self.assertIn(expected, response.context)
                self.data_for_test_of_context(response, single_page)

    def test_first_page_contains_ten_records(self):
        """Проверка пагинатора для первой страницы."""
        cache.clear()
        for reverse_name, _, single_page in self.url:
            if single_page is False:
                with self.subTest(reverse_name=reverse_name):
                    response = self.authorized_client.get(reverse_name)
                    self.assertEqual(
                        len(response.context['page_obj']), QUANTITY
                    )

    def test_last_page_records_contains_n_recodrds(self):
        """Проверка пагинатора для последней страницы."""
        cache.clear()
        for reverse_name, _, single_page in self.url:
            if single_page is False:
                with self.subTest(reverse_name=reverse_name):
                    response = self.authorized_client.get(
                        reverse_name
                        + f'?page={self.pages_amount}'
                    )
                    self.assertEqual(len(
                        response.context['page_obj']),
                        self.posts_amount_of_last_page
                    )


class TestViewsCreation(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HaHaHa')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='group-slug'
        )
        cls.another_group = Group.objects.create(
            title='Иной тестовый заголовок',
            description='Иное тестовое описание',
            slug='group-another-slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

        cls.reverse_pages = (
            reverse(
                'posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}),
            reverse(
                'posts:profile',
                kwargs={'username': cls.post.author.username}),
        )
        cls.reverse_group_pages = {
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}): 1,
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.another_group.slug}): 0,
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_another_post_appearance_after_creation(self):
        """Проверка появления нового поста с указанием группы на страницах:
            главная, посты группы, посты автора. Проверка, что пост не
            отображается на странице другой группы"""
        cache.clear()
        for path in self.reverse_pages:
            response = self.authorized_client.get(path)
            self.assertEqual(
                response.context['page_obj'][0].group, self.post.group
            )
        for group_path, value in self.reverse_group_pages.items():
            with self.subTest(group_path=group_path):
                response = self.authorized_client.get(group_path)
                self.assertEqual(
                    len(response.context['page_obj']), value
                )


class TestViewsCommentFollow(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HaHaHa')
        cls.follower = User.objects.create_user(username='Alice')
        cls.hater = User.objects.create_user(username='Hater')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )
        cls.follow = Follow.objects.create(
            user=cls.follower,
            author=cls.user
        )
        cls.another_post = Post.objects.create(
            author=cls.follower,
            text='Тестовый другой текст',
        )
        cls.another_follow = Follow.objects.create(
            user=cls.hater,
            author=cls.follower
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый комментарий',
            author=cls.follower,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.follower)
        self.authorized_hater = Client()
        self.authorized_hater.force_login(self.hater)

    def test_post_comments_list_change(self):
        """Проверка появления нового комментария под целевым постом
           и его отсутствия под другим постом."""
        cache.clear()
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(
            response.context['comments'][0], self.comment
        )
        response1 = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.another_post.id}))
        self.assertNotEqual(
            response1.context.get('comment'), self.comment
        )

    def test_follower_posts_list_changes(self):
        """Проверка появления нового поста в ленте подписчика
            и его отсутствия в ленте другого пользователя."""
        cache.clear()
        response = self.authorized_follower.get(reverse(
            'posts:follow_index'))
        self.assertIn(self.post, response.context['page_obj'])
        response = self.authorized_hater.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_authorized_user_access_to_follow(self):
        """Авторизованный пользователь может подписываться
            на других пользователей."""
        response = self.authorized_client.get(reverse(
            'posts:follow_index'))
        self.assertNotIn(self.another_post, response.context['page_obj'],
                         ('Пост автора уже есть в ленте пользователя'
                         'до подписки на этого автора.'))
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.follower})
        )
        response = self.authorized_client.get(reverse(
            'posts:follow_index')
        )
        self.assertIn(self.another_post, response.context['page_obj'],
                      ('После подписки на автора,'
                      'его пост не появился в ленте подписок.'))
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.follower}))
        self.assertTrue(response.context.get('following'),
                        ('Пользователь уже подписан на автора,'
                        'но ему доступна повторная подписка.'))

    def test_authorized_user_access_to_unfollow(self):
        """Авторизованный пользователь может отписываться
            от других пользователей."""
        response = self.authorized_hater.get(reverse(
            'posts:profile', kwargs={'username': self.user}))
        self.assertFalse(response.context.get('following'),
                         ('Пользователь не подписан на автора, '
                         'но ему доступна функция удаления подписки.'))
        response = self.authorized_hater.get(reverse(
            'posts:follow_index'))
        self.assertIn(self.another_post, response.context['page_obj'],
                      ('Пользователь подписан на автора, но пост автора не'
                      'отображается в ленте до удаления подписки на него.'))
        self.authorized_hater.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.follower}))
        response = self.authorized_follower.get(reverse(
            'posts:follow_index'))
        self.assertNotIn(self.another_post, response.context['page_obj'],
                         ('После удаления подписки на автора, '
                         'его пост отображаются в ленте подписок.'))

    def test_follow_redirecs(self):
        """После подписки/отписки выполняется переход
            на страницу автора/главную страницу."""
        urls = {
            reverse(
                'posts:profile_follow', kwargs={'username': self.follower}):
                    f'/profile/{self.follower}/',
            reverse(
                'posts:profile_unfollow', kwargs={'username': self.follower}):
                    '/',
        }
        for url, value in urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertRedirects(response, value)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

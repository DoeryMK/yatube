import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HaHaHa')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='group-slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.post_count = Post.objects.count()
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def data_for_test_of_post_form(self, form_data):
        last_post = Post.objects.all().first()
        self.assertEqual(last_post.author, form_data['author'])
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group.pk, form_data['group'])
        uploaded_image = form_data['image'].name
        self.assertEqual(last_post.image, f'posts/{uploaded_image}')

    def test_create_post(self):
        """Валидная форма создает новый пост."""
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'author': self.user,
            'text': self.post.text,
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), self.post_count + 1)
        self.assertTrue(Post.objects.filter(
            author=self.user,
            text=self.post.text,
            group=self.group.pk,
            image=f'posts/{uploaded.name}'
        ).exists(), ('Пост не был создан'))
        self.data_for_test_of_post_form(form_data)

    def test_edite_post(self):
        """Валидная форма редактирует существующий пост."""
        uploaded = SimpleUploadedFile(
            name='big.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'author': self.user,
            'text': 'Совсем новый текст',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), self.post_count)
        self.assertTrue(Post.objects.filter(
            author=self.user,
            text='Совсем новый текст',
            group=self.group.pk,
            image=f'posts/{uploaded.name}'
        ).exists())
        self.data_for_test_of_post_form(form_data)

    def test_held_text_and_label(self):
        """Проверка содержания help_text, label в форме."""
        expected_values = {
            'text': ('Текст поста', 'Текст нового поста'),
            'group': ('Группа: ', 'Группа, к которой будет относиться пост'),
        }
        for attr, values in expected_values.items():
            with self.subTest(attr=attr):
                label = PostFormTests.form.fields[attr].label
                self.assertEqual(label, values[0])
                help_text = PostFormTests.form.fields[attr].help_text
                self.assertEqual(help_text, values[1])


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HaHaHa')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )
        cls.comment_count = Comment.objects.count()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        """Валидная форма создает новый комментарий."""
        form_data = {
            'post': self.post,
            'text': 'Другой тестовый комментарий',
            'author': self.comment.author,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), self.comment_count + 1)
        self.assertTrue(Comment.objects.filter(
            post=self.post,
            text=form_data['text'],
            author=self.comment.author
        ).exists(), ('Пост не был создан'))

    def test_ignore_comment(self):
        """Форма не создает комментарий неавторизованного пользователя."""
        form_data = {
            'text': 'Третий тестовый комментарий',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertNotIn(form_data['text'], response.content.decode())
        self.assertEqual(Comment.objects.count(), self.comment_count)

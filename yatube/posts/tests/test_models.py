from django.test import TestCase

from posts.models import Comment, Follow, Group, Post, User

QUANTITY = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HaHaHa')
        cls.follower = User.objects.create_user(username='Alice')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый постпостпост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.follower,
            text='Тестовый комментарий'
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.follower
        )
        cls.data = {
            str(cls.post): cls.post.text[:QUANTITY],
            str(cls.group): cls.group.title,
            str(cls.comment): cls.comment.text[:QUANTITY],
            str(cls.follow):
            f'{cls.follow.user.username}, {cls.follow.author.username}',
        }

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        for method, value in PostModelTest.data.items():
            with self.subTest(method=method):
                self.assertEqual(method, value)

    def test_verbose_names(self):
        """verbose_name, help_text в моделях совпадает с ожидаемым."""
        data = {
            PostModelTest.post: {
                'text': ('Содержание публикации', 'Введите текст поста',),
                'pub_date': ('Дата публикации',
                             ''),
                'author': ('Автор',
                           ''),
                'group': ('Группа',
                          'Выберите группу'),
                'image': ('Изображение',
                          'Загрузите картинку'),
            },
            PostModelTest.group: {
                'title': ('Название группы',
                          ''),
                'slug': ('URL',
                         ''),
                'description': ('Описание тематики группы',
                                ''),
            },
            PostModelTest.comment: {
                'post': ('Комментарий',
                         'Оставьте комментарий',),
                'author': ('Автор комментария', ''),
                'text': ('Содержание комментария',
                         'Введите текст комментария',),
                'created': ('Дата и время публикации',
                            ''),
            },
            PostModelTest.follow: {
                'user': ('Подписчик',
                         ''),
                'author': ('Автор классных постов',
                           ''),
            }
        }

        for entity, verbose in data.items():
            for field, expected_value in verbose.items():
                with self.subTest(field=field):
                    self.assertEqual(
                        entity._meta.get_field(field).verbose_name,
                        expected_value[0]
                    )
                    self.assertEqual(
                        entity._meta.get_field(field).help_text,
                        expected_value[1]
                    )

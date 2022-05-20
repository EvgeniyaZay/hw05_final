import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse


from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slag',
            description='Тестовое описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html':
                reverse('posts:group_list',
                        kwargs={'slug': f'{self.group.slug}'}
                        ),
            'posts/profile.html':
                reverse('posts:profile',
                        kwargs={'username': f'{self.post.author}'}
                        ),
            'posts/create_post.html': reverse('posts:post_create'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """проверка index"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_group_list_pages_show_correct_context(self):
        """Проверка group_list на правильность контекста."""
        response = (self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}))
                    )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.group.title, self.group.title)
        self.assertEqual(first_object.group.slug, self.group.slug)
        self.assertEqual(first_object.group.description,
                         self.group.description
                         )
        self.assertEqual(first_object.image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Проверка profile на правильность контекста."""
        response = (self.authorized_client.get(

            reverse('posts:profile',

                    kwargs={'username': f'{self.post.author}'}))
                    )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Проверка post_detail на правильность контекста"""
        response = (self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{self.post.id}'}))
                    )
        # self.assertEqual(response.context['author'], self.user)
        self.assertEqual(response.context.get('post').author.username,
                         f'{self.post.author}')
        self.assertEqual(response.context.get('post').text, 'Текст поста')
        self.assertEqual(response.context.get('post').group.title,
                         f'{self.group}')
        self.assertEqual(
            response.context.get('post').image,
            f'{self.post.image}'
        )

    def test_cache(self):
        response = self.authorized_client.get(reverse('posts:index'))
        content_post = response.content
        Post.objects.get(id=self.post.id).delete()
        response = self.authorized_client.get(reverse('posts:index'))
        # cache.clear()
        self.assertEqual(content_post, response.content)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(content_post, response.content)


    def test_profile_follow(self):
        """проверка что пользователь не подписан на автора поста"""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj']
        self.assertEqual(0, len(first_object))

        """подписываемся на автора поста"""
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.post.author})
        )

        """проверка что пользователь подписался"""
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        second_object = response.context['page_obj']
        self.assertEqual(0, len(second_object))

    def test_profile_unfollow(self):
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.post.author})
        )

        response = self.authorized_client.get(reverse('posts:follow_index'))
        page_object = response.context['page_obj']
        self.assertEqual((len(page_object)), 0)

        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.post.author})
        )

        response = self.authorized_client.get(reverse('posts:follow_index'))
        page_object = response.context['page_obj']
        self.assertEqual((len(page_object)), 0)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        post_list = [Post(author=cls.user,
                          group=cls.group,
                          text=str(i))
                     for i in range(13)]

        Post.objects.bulk_create(post_list)

    def setUp(self):
        self.authorized_client = Client()

    def test_paginator_pages(self):
        POST_ON_FIRST_PAGE = settings.MAX_PAGE_AMOUNT
        POST_ON_ALL_PAGE = 13 - POST_ON_FIRST_PAGE

        """Проверка: количество постов на первой странице равно 10."""
        response = self.authorized_client.get(reverse('posts:index'))
        list_test = response.context['page_obj']
        list_test.paginator.count
        self.assertEqual(POST_ON_FIRST_PAGE, len(list_test))

        """Проверка: на второй странице должно быть три поста."""
        response = self.client.get(reverse('posts:index') + '?page=2')
        list_test = response.context['page_obj']
        list_test.paginator.count
        self.assertEqual(POST_ON_ALL_PAGE, len(list_test))

        """проверка пагинации на страницах"""
        list_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]

        for lists in list_pages:
            with self.subTest():
                response = self.authorized_client.get(lists)
                list_test = response.context['page_obj']
                list_test.paginator.count
                self.assertEqual(POST_ON_FIRST_PAGE, len(list_test))

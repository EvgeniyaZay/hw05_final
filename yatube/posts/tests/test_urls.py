from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Post, Group

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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.urls = (
            '/',
            '/group/test_slag/',
            f'/profile/{cls.user}/',
            '/create/',
            f'/posts/{cls.post.id}/'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)

    def test_urls_for_authorized_exists(self):
        """Доступность url адресов для авторизованных пользователей."""
        for url in self.urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_url_for_author_exists(self):
        """Cтраница редактирования для автора поста post_detail"""
        urls = (
            '/create/',
            f'/posts/{self.post.id}/'
        )
        for url in urls:
            with self.subTest():
                response = self.authorized_client_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_guest_client_exists(self):
        """Страница для неавторизованных пользователей."""
        for url in self.urls:
            with self.subTest():
                response = self.guest_client.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        template_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in template_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_404_page(self):
        """Запрос к несуществующей странице вернёт ошибку 404"""
        response = self.guest_client.get('/n0t_ex15ting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

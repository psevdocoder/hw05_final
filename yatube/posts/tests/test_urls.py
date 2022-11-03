from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.no_author = User.objects.create_user(username='no_author')

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.no_author_client = Client()
        self.no_author_client.force_login(self.no_author)
        self.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовый текст',
        )
        self.post = Post.objects.create(
            author=self.author,
            group=self.group,
            text='Тестовый заголовок',
            pub_date='25.10.2022',
        )

    def test_pages_exists_at_desired_location(self):
        """Страница доступна любому пользователю."""
        pages_url = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.author}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }

        for address, http_status in pages_url.items():
            with self.subTest(adress=address):
                response = Client().get(address)
                self.assertEqual(response.status_code, http_status)

    def test_post_edit_url_redirect_anonymous(self):
        """Страница post_edit/ перенаправляет анонимного пользователя."""
        response = Client().post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertRedirects(response, '/auth/login/?next=/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_create_url_redirect_anonymous(self):
        """Страница create/ перенаправляет анонимного пользователя."""
        response = Client().post(reverse('posts:post_create'))
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/post_detail.html': reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}),
            'posts/group_list.html': reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse(
                'posts:profile', kwargs={'username': self.author.username}),
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница posts/<post_id>/edit/ доступна автору поста."""
        response = self.author_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unknown_page_url_unexists_at_desired_location(self):
        """Страница не существует и используется кастомный шаблон."""
        response = Client().get('/none/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_no_author_of_post_cant_edit_post(self):
        """Страница posts/<post_id>/edit/ не доступна
         авторизованному пользователю, но не автору поста."""
        response = self.no_author_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_comments_access_for_not_auth_clients(self):
        """
        Тестирование, что неавторизованный клиент не
        может оставлять комментарии.
        """
        response = Client().get(
            reverse('posts:add_comment', args=(self.post.id,))
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/comment/')

    def test_comments_access_for_auth_users(self):
        """
        Тестирование, что авторизованный клиент может оставлять комментарии.
        """
        response = self.no_author_client.get(
            reverse('posts:add_comment', args=(self.post.id,))
        )
        self.assertEqual(
            response.status_code, HTTPStatus.FOUND)

    def test_access_to_follows_for_auth_user(self):
        """
        Тестирование, что авторизованный клиент может подписываться и
        отписываться на других.
        """
        response_follow = self.no_author_client.get(
            reverse('posts:profile_follow', args=(self.author.username,))
        )
        self.assertEqual(response_follow.status_code, HTTPStatus.FOUND)
        response_unfollow = self.no_author_client.get(
            reverse('posts:profile_unfollow', args=(self.author.username,))
        )
        self.assertEqual(response_unfollow.status_code, HTTPStatus.FOUND)

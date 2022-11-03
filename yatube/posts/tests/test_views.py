import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django import forms
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .utils import create_post_with_photo
from ..models import Group, Post, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='title',
            slug='slug',
            description='description'
        )

    def setUp(self):
        self.author = User.objects.create_user(username='auth')
        self.auth_client = Client()
        self.auth_client.force_login(self.author)

        self.follower = User.objects.create_user(username='follower')
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

        self.not_follower = User.objects.create_user(username='not_follower')
        self.not_follower_client = Client()
        self.not_follower_client.force_login(self.not_follower)

        self.post = Post.objects.create(
            text='Test post',
            author=self.author,
            group=self.group
        )

        Follow.objects.create(
            author=self.author,
            user=self.follower
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_namespace(self):
        """Тестирование namespace:name."""
        pages = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': self.author.username}),
            'posts/post_detail.html': reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}),
            'posts/create_post.html': reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}),
        }

        for template, reverse_name in pages.items():
            with self.subTest(template=template):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

        response = self.auth_client.get(reverse('posts:post_create'))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_context_on_index(self):
        """Тестирование содержимого index страницы."""
        response = self.auth_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.post_test(post)

    def test_context_and_group_list(self):
        """Тестирование содержимого group_list страницы и проверка,
        что пост в группе."""
        response = self.auth_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))

        post = response.context['page_obj'][0]
        self.post_test(post)

        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)

    def test_another_group_list(self):
        """Тестирование, что пост не добавлен в другую группу."""
        self.another_group = Group.objects.create(
            title='not title',
            slug='not-slug',
            description='not description'
        )
        another_response = self.auth_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.another_group.slug})
        )
        another_group_post = another_response.context['page_obj']
        self.assertNotEqual(another_group_post, self.post)

    def test_context_profile(self):
        """Тестирование содержимого profile страницы."""
        response = self.auth_client.get(
            reverse('posts:profile', kwargs={'username': self.author.username})
        )
        post = response.context['page_obj'][0]
        self.post_test(post)
        author = response.context['author']
        self.assertEqual(author.username, self.author.username)

    def test_context_post_detail(self):
        """Тестирование содержимого post_detail."""

        response = self.auth_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context['post']
        self.post_test(post)

    def test_context_and_form_create_post(self):
        """Тестирование содержимого create_post при создании поста."""
        expected_form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }

        response = self.auth_client.get(reverse('posts:post_create'))
        for value, expected in expected_form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        context_is_edit = response.context['is_edit']
        self.assertEqual(context_is_edit, False)

    def test_context_and_form_edit_post(self):
        """Тестирование содержимого edit_post при изменении поста."""
        expected_form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        response = self.auth_client.get(
            reverse('posts:post_edit', args=(self.post.id,)))
        for value, expected in expected_form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

            context_is_edit = response.context['is_edit']
            self.assertEqual(context_is_edit, True)

    def test_photo_in_context(self):
        """Проверка наличия фото в словаре контекста."""

        create_post_with_photo(self)

        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', args=(self.group.slug,)),
            reverse('posts:profile', args=(self.author.username,)),
            reverse('posts:post_detail', args='2'),
        ]

        for page in pages:
            with self.subTest(page=page):
                response = self.auth_client.get(page)
                self.assertContains(response, '<img')

    def test_paginator(self):
        """Тестирование паджинатора на разных страницах."""
        self.POSTS_ON_PAGE_1 = 10
        self.POSTS_ON_PAGE_2 = 6

        self.posts = Post.objects.bulk_create(
            Post(
                author=self.author,
                text=f'тестовый пост {i + 1}',
                group=self.group
            )
            for i in range(self.POSTS_ON_PAGE_1 + self.POSTS_ON_PAGE_2 - 1))

        responses = [
            reverse('posts:index'),
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            ),
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        ]

        for response in responses:
            with self.subTest(response=response):
                page_1_response = self.client.get(response)
                self.assertEqual(
                    len(page_1_response.context['page_obj']),
                    self.POSTS_ON_PAGE_1
                )
                page_2_response = self.client.get(response + '?page=2')
                self.assertEqual(
                    len(page_2_response.context['page_obj']),
                    self.POSTS_ON_PAGE_2
                )

    def post_test(self, post):
        """Вспомогательная функция тестирования постов."""
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.author, self.post.author)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response_before_add = self.auth_client.get(reverse('posts:index'))
        Post.objects.create(
            text='test_new_post',
            author=self.author,
        )
        response_after_add = self.auth_client.get(reverse('posts:index'))
        self.assertEqual(
            response_after_add.content,
            response_before_add.content
        )
        cache.clear()
        response_after_clean = self.auth_client.get(reverse('posts:index'))
        self.assertNotEqual(
            response_after_add.content,
            response_after_clean.content
        )

    def test_new_post_on_follow_page(self):
        """Проверка появления нового поста в ленте у подписчика."""
        response = self.follower_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post, self.post)

    def test_new_post_not_on_follow_page(self):
        """
        Тестирование, что нового поста нет в ленте у не подписанного
        пользователя.
        """
        response = self.not_follower_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj']
        self.assertNotEqual(post, self.post)

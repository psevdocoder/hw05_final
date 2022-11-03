from django.contrib.auth import get_user_model
from ..forms import PostForm
from ..models import Group, Post, Comment
import shutil
import tempfile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовый текст',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def TearDown(self):
        del self.post

    def setUp(self):
        self.auth_user = User.objects.create_user(username='auth_user')
        self.auth_client = Client()
        self.auth_client.force_login(self.auth_user)

    def test_create_post_form(self):
        """Проверка редиректа и создания новой записи в базе данных."""
        posts_count = Post.objects.count()

        from .utils import create_post_with_photo
        response = create_post_with_photo(self)

        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.auth_user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text='123',
                id=1,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post_form(self):
        """Проверка редиректа и редактирования поста."""

        form_data = {
            'text': 'тестовый текст',
            'group': self.group.id
        }
        self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )

        new_form_data = {
            'text': 'тестовый текст new',
            'group': self.group.id
        }
        response = self.auth_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=new_form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        self.assertTrue(
            Post.objects.filter(
                text='тестовый текст new',
                id=1,
            ).exists()
        )

    def test_comment_creation(self):
        """После успешной отправки комментарий появляется на странице поста."""
        self.post = Post.objects.create(
            author=self.auth_user,
            group=self.group,
            text='Тестовый текст',
        )

        form_data = {
            'text': 'Somebody, save me from tests...'
        }

        comments_count = Comment.objects.filter(post_id=self.post.id).count()

        self.auth_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            Comment.objects.filter(post_id=self.post.id).count(),
            comments_count + 1)
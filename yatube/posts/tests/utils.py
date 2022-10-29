from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse


def create_post_with_photo(self):
    small_gif = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00'
        b'\x01\x00\x00\x00\x00\x21\xf9\x04'
        b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
        b'\x00\x00\x01\x00\x01\x00\x00\x02'
        b'\x02\x4c\x01\x00\x3b'
    )
    uploaded = SimpleUploadedFile(
        name='small.gif',
        content=small_gif,
        content_type='image/gif',
    )

    form_data = {
        'text': '123',
        'group': self.group.id,
        'image': uploaded,
    }

    response = self.auth_client.post(
        reverse('posts:post_create'),
        data=form_data,
        follow=True
    )

    return response

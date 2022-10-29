from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta(forms.ModelForm):
        model = Post
        fields = ('text', 'group', 'image')

        def clean_text_validator(self):
            text = self.cleaned_data['text']
            if text == '':
                raise forms.ValidationError(
                    'Текст записи не должен быть пустым'
                )
            return text


class CommentForm(forms.ModelForm):
    class Meta(forms.ModelForm):
        model = Comment
        fields = ('text',)

        def clean_text_validator(self):
            text = self.cleaned_data['text']
            if text == '':
                raise forms.ValidationError(
                    'Текст поста не должен быть пустым'
                )
            return text

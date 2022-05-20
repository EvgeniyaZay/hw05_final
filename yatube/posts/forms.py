from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        labels = {'group': 'Группа', 'text': 'Сообщение', 'image': 'Изображение'}
        help_texts = {'group': 'Выберите группу', 'text': 'Введите ссообщение'}
        fields = ["group", "text", "image"]


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        labels = {'text': 'Комментарий'}
        help_texts = {'text': 'Введите текст комментария'}
        fields = ['text']


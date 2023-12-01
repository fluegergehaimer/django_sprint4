from django import forms

from blog.models import User, Post, Comment


class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ('author', 'created_at',)


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from blog.forms import CommentForm, PostForm, UserForm
from blog.models import Category, Comment, Post, User

POSTS_PER_PAGE = 10


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.get_username()}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class EditView(LoginRequiredMixin):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs[self.pk_url_kwarg]
            )
        return super().dispatch(request, *args, **kwargs)


def posts_selection(posts):
    return posts.select_related(
        'category',
        'location',
        'author',
    ).annotate(
        comment_count=Count('comments')
    ).order_by(
        '-pub_date'
    )


def published_posts(posts):
    return posts_selection(posts).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    )


class PostUpdateView(EditView, UpdateView):
    form_class = PostForm

    def get_context_data(self, **kwargs):
        return dict(**(super().get_context_data(**kwargs)), is_edit=True)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.get_object().pk}
        )


class PostDeleteView(EditView, DeleteView):
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        return dict(**(super().get_context_data(**kwargs)), is_delete=True)


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    paginate_by = POSTS_PER_PAGE
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            form=CommentForm(),
            comments=(self.object.comments.select_related('post'))
        )

    def get_queryset(self):
        self.post_data = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if self.post_data.author == self.request.user:
            return posts_selection(Post.objects).filter(
                pk=self.kwargs['post_id']
            )
        return published_posts(Post.objects).filter(
            pk=self.kwargs['post_id']
        )


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = POSTS_PER_PAGE

    def get_context_data(self, **kwargs):
        return dict(
            **(super().get_context_data(**kwargs)),
            category=get_object_or_404(
                Category,
                slug=self.kwargs['category_slug'],
                is_published=True,
            )
        )

    def get_queryset(self):
        return published_posts(
            get_object_or_404(
                Category,
                slug=self.kwargs.get('category_slug'),
                is_published=True
            ).posts
        )


class ProfileListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = POSTS_PER_PAGE

    def get_context_data(self, **kwargs):
        return dict(
            **(super().get_context_data(**kwargs)),
            profile=get_object_or_404(
                User,
                username=self.kwargs.get('username')
            )
        )

    def get_queryset(self):
        return posts_selection(
            get_object_or_404(
                User,
                username=self.kwargs.get('username')
            ).posts
        )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'
    success_url = reverse_lazy('blog:index')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username})


class CommentMixin:
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect(
                'blog:post_detail',
                self.kwargs.get('post_id')
            )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.comment = get_object_or_404(
            Post,
            pk=self.kwargs['post_id']
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs.get('post_id')}
        )


class CommentUpdateView(LoginRequiredMixin, CommentMixin, UpdateView):

    def get_context_data(self, **kwargs):
        return dict(**(super().get_context_data(**kwargs)), is_edit=True)


class CommentDeleteView(LoginRequiredMixin, CommentMixin, DeleteView):

    def get_context_data(self, **kwargs):
        return dict(**(super().get_context_data(**kwargs)), is_delete=True)


class IndexListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = POSTS_PER_PAGE
    queryset = published_posts(Post.objects)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        commentary = form.save(commit=False)
        commentary.author = request.user
        commentary.post = post
        commentary.save()
    return redirect('blog:post_detail', post_id=post_id)

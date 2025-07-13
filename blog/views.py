from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from .models import Post, Category, Tag, Comment
from .forms import CommentForm
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.text import slugify


# category_page함수는 FBV로 만들었다.
def category_page(request, slug):
    if slug == 'no_category':
        category = '미분류'
        post_list = Post.objects.filter(category=None)
    else:
        category = Category.objects.get(slug=slug)
        post_list = Post.objects.filter(category=category)

    return render(
        request,
        'blog/post_list.html',
        {
            'post_list': post_list,
            'categories': Category.objects.all(),
            'no_category_post_count': Post.objects.filter(category=None).count(),
            'category': category,
        }
    )


def tag_page(request, slug):
    tag = Tag.objects.get(slug=slug)
    post_list = tag.post_set.all()

    return render(
        request,
        'blog/post_list.html',
        {
            'post_list': post_list,
            'tag': tag,
            'categories': Category.objects.all(),
            'no_category_post_count': Post.objects.filter(category=None).count(),
        }
    )


def new_comment(request, pk):
    if request.user.is_authenticated:  # 로그인이 되어있지 않다면 댓글 폼 안보임
        post = get_object_or_404(Post, pk=pk)  # pk를 인자로 받고, 댓글을 달 post를 쿼리로 날려 가져옴. 없을 경우 404 에러

    if request.method == 'POST':  # submit 버튼 누르면 POST 방식으로 데이터 전달
        comment_form = CommentForm(request.POST)  # 정상적으로 폼 작성후 POST 했다면 해당 정보를 commentForm 형태로 가져옴
        if comment_form.is_valid():  # 폼이 유효하게 작성되었을 경우 새로운 레코드를 만들어 DB에 저장
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect(comment.get_absolute_url())  # 마지막으로 comment의 URL로 리다이렉트.
        else:  # 브라우저에서 바로 127.0.0.1:8000/10/new_comment/로 작성해서 요청하는 경우 
            return redirect(post.get_absolute_url())
    else:  # 로그인 되어있지 않은 데다가 비정상접근을 시도한다면 접근 거부
        raise PermissionDenied


class CommentUpdate(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user == self.get_object().author:
            return super(CommentUpdate, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied


def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post = comment.post
    if request.user.is_authenticated and request.user == comment.author:
        comment.delete()
        return redirect(post.get_absolute_url())
    else:
        raise PermissionDenied


class PostUpdate(LoginRequiredMixin, UpdateView):
    model = Post  # Post 모델을 사용한다.
    fields = ['title', 'hook_text', 'content', 'head_image', 'file_upload', 'category']  # 태그가 2개로 보여서 하나 지웠다
    # fields = ['title', 'hook_text', 'content', 'head_image', 'file_upload', 'category',
    #           'tags']  # Post 모델에 사용할 필드명들은 다음과 같다. (기존 코드)

    template_name = 'blog/post_update_form.html'

    def get_context_data(self, **kwargs):
        context = super(PostUpdate, self).get_context_data()
        if self.object.tags.exists():
            tags_str_list = list()
            for t in self.object.tags.all():
                tags_str_list.append(t.name)
            context['tags_str_default'] = '; '.join(tags_str_list)
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user == self.get_object().author:
            return super(PostUpdate, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def form_valid(self, form):
        response = super(PostUpdate, self).form_valid(form)
        self.object.tags.clear()

        tags_str = self.request.POST.get('tags_str')
        if tags_str:
            tags_str = tags_str.strip()
            tags_str = tags_str.replace(',', ';')
            tags_list = tags_str.split(';')

            for t in tags_list:
                t = t.strip()
                tag, is_tag_created = Tag.objects.get_or_create(name=t)
                if is_tag_created:
                    tag.slug = slugify(t, allow_unicode=True)
                    tag.save()
                self.object.tags.add(tag)
        return response


class PostCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post  # Post 모델을 사용한다.
    fields = ['title', 'hook_text', 'content', 'head_image', 'file_upload', 'category']  # Post 모델에 사용할 필드명들은 다음과 같다.

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff  # superuser 또는 staff 권한이 있는 사용자만 게시물 작성할 수 있도록

    def form_valid(self, form):
        current_user = self.request.user  # 웹 사이트의 방문자
        if current_user.is_authenticated and (
                current_user.is_staff or current_user.is_superuser):  # is_authenticated는 사용자가 로그인했는지 확인하는 속성이다.
            form.instance.author = current_user
            response = super(PostCreate, self).form_valid(form)

            tags_str = self.request.POST.get('tags_str')  # POST 방식으로 전달된 정보 중 name='tags_str'인 input값을 가져와라 
            if tags_str:
                tags_str = tags_str.strip()

                tags_str = tags_str.replace(',', ';')
                tags_list = tags_str.split(';')

                for t in tags_list:
                    t = t.strip()
                    tag, is_tag_created = Tag.objects.get_or_create(name=t)
                    if is_tag_created:
                        tag.slug = slugify(t, allow_unicode=True)
                        tag.save()
                    self.object.tags.add(tag)  # self.object는 이번에 새로 만들어지는 post를 의미함

                return response
        else:
            return redirect('/blog/')


class PostList(ListView):
    model = Post
    ordering = '-pk'  # pk 값이 큰 순서대로. 측 최신의 글 순서대로 보여달라는 의미, -는 역순의 의미
    paginate_by = 5

    def get_context_data(self, **kwargs):
        context = super(PostList, self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count'] = Post.objects.filter(category=None).count()
        return context


class PostDetail(DetailView):
    model = Post

    def get_context_data(self, **kwargs):
        context = super(PostDetail, self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count'] = Post.objects.filter(category=None).count()
        context['comment_form'] = CommentForm
        return context

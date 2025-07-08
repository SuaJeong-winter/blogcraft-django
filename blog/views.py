from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Post, Category, Tag
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


class PostUpdate(LoginRequiredMixin, UpdateView):
    model = Post  # Post 모델을 사용한다.
    fields = ['title', 'hook_text', 'content', 'head_image', 'file_upload', 'category',
              'tags']  # Post 모델에 사용할 필드명들은 다음과 같다.

    template_name = 'blog/post_update_form.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user == self.get_object().author:
            return super(PostUpdate, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied


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
    ordering = '-pk'

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
        return context

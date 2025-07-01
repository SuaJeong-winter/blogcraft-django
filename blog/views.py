from django.shortcuts import render
from django.views.generic import ListView
from .models import Post

class PostList(ListView):
    model= Post
    ordering = '-pk'

def single_post_page(request,pk):
    post = Post.objects.get(pk=pk)

    return render(
        request,
        'blog/single_post_page.html',
        {
            'post': post,
        }
    )
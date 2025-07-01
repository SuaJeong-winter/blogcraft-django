from django.views.generic import ListView,DetailView
from .models import Post
from django.shortcuts import render
from django.conf import settings

class PostList(ListView):
    model= Post
    ordering = '-pk'

class PostDetail(DetailView):
    model= Post


from django.test import TestCase, Client
from django.contrib.auth.models import User
from bs4 import BeautifulSoup
from blog.models import Post
# allauth 오류 해결용
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


class TestView(TestCase):
    def setUp(self):
        self.client = Client()
        # allauth 오류 해결용
        site, _ = Site.objects.get_or_create(id=1, defaults={'domain': 'testserver', 'name': 'testserver'})

        if not SocialApp.objects.filter(provider='google').exists():
            google_app = SocialApp.objects.create(
                provider='google',
                name='Google',
                client_id='fake-client-id',
                secret='fake-secret'
            )
            google_app.sites.add(site)
        # 여기까지

        self.user_milan = User.objects.create_user(username='milan', password='1234Arabbit')

    def test_landing(self):
        post_001 = Post.objects.create(
            title='첫번째 포스트',
            content='첫번째 포스트입니다.',
            author=self.user_milan
        )

        post_002 = Post.objects.create(
            title='두번째 포스트',
            content='두번째 포스트입니다.',
            author=self.user_milan
        )

        post_003 = Post.objects.create(
            title='세번째 포스트',
            content='세번째 포스트입니다.',
            author=self.user_milan
        )

        post_004 = Post.objects.create(
            title='네번째 포스트',
            content='네번째 포스트입니다.',
            author=self.user_milan
        )

        response = self.client.get('')
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        body = soup.body
        self.assertNotIn(post_001.title, body.text)
        self.assertIn(post_002.title, body.text)
        self.assertIn(post_003.title, body.text)
        self.assertIn(post_004.title, body.text)

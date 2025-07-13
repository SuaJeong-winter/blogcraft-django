from django.test import TestCase, Client
from bs4 import BeautifulSoup
from django.contrib.auth.models import User  # User모델을 사용하기 위함
from .models import Post, Category, Tag, Comment
# allauth.socialaccount.models.SocialApp.DoesNotExist 오류 해결용 코드
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


class TestView(TestCase):
    def setUp(self):  # setUp() 함수는 TestCase의 초기 데이터베이스 상태를 정의할 수 있다.
        # allauth.socialaccount.models.SocialApp.DoesNotExist 오류 해결용 코드
        # Site과 SocialApp이 테스트 DB에 없으면 생성
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

        self.client = Client()
        self.user_milan = User.objects.create_user(username='milan', password='1234Arabbit')
        self.user_ain = User.objects.create_user(username='ain', password='somepassword')

        self.user_milan.is_staff = True  # milan에게 staff 권한을 부여
        self.user_milan.save()

        self.category_programming = Category.objects.create(name='programming', slug='programming')
        self.category_react = Category.objects.create(name='react', slug='react')

        # Tag 모델에 대한 테스트 데이터(파이썬 공부, python, hello) 생성
        self.tag_python_kor = Tag.objects.create(name='파이썬 공부', slug='파이썬-공부')
        self.tag_python = Tag.objects.create(name='python', slug='python')
        self.tag_hello = Tag.objects.create(name='hello', slug='hello')

        self.post_001 = Post.objects.create(
            title='첫번째 포스트입니다.',
            content="hello world! we are the world",
            category=self.category_programming,
            author=self.user_milan
        )
        self.post_001.tags.add(self.tag_hello)

        self.post_002 = Post.objects.create(
            title='두번째 포스트입니다.',
            content="this is second post",
            category=self.category_react,
            author=self.user_ain
        )

        self.post_003 = Post.objects.create(
            title='세번째 포스트입니다.',
            content="no category content",
            author=self.user_ain
        )
        self.post_003.tags.add(self.tag_python_kor)
        self.post_003.tags.add(self.tag_python)

        self.comment_001 = Comment.objects.create(
            post=self.post_001,
            author=self.user_milan,
            content='첫번째 댓글입니다.'
        )

    def test_tag_page(self):
        response = self.client.get(self.tag_hello.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        self.navbar_test(soup)
        self.category_card_test(soup)

        self.assertIn(self.tag_hello.name, soup.h1.text)

        main_area = soup.find('div', id='main-area')
        self.assertIn(self.tag_hello.name, main_area.text)

        self.assertIn(self.post_001.title, main_area.text)
        self.assertNotIn(self.post_002.title, main_area.text)
        self.assertNotIn(self.post_003.title, main_area.text)

    def test_category_page(self):
        # 페이지가 잘 열리는지 확인
        response = self.client.get(self.category_programming.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        # 페이지에 카테고리 이름이 있는지 확인
        soup = BeautifulSoup(response.content, 'html.parser')
        self.navbar_test(soup)
        self.category_card_test(soup)
        # 카테고리 뱃지가 페이지 제목에 잘 나타나는지 
        self.assertIn(self.category_programming.name, soup.h1.text)
        # 카테고리의 이름과 그 카테고리에
        #
        # 해당하는 포스트만 나타나고 있는지 확인
        main_area = soup.find('div', id='main-area')
        self.assertIn(self.category_programming.name, main_area.text)
        self.assertIn(self.post_001.title, main_area.text)
        self.assertNotIn(self.post_002.title, main_area.text)
        self.assertNotIn(self.post_003.title, main_area.text)

    def category_card_test(self, soup):  # id가 category-card인 div 요소를 찾고 모든 카테고리가 제대로 출력되어 있는지 확인
        categories_card = soup.find('div', id='categories-card')
        self.assertIn('Categories', categories_card.text)
        self.assertIn(f'{self.category_programming.name} ({self.category_programming.post_set.count()})',
                      categories_card.text)
        self.assertIn(f'미분류(1)', categories_card.text)

    def navbar_test(self, soup):
        # 1.4 네비게이션 바가 있다.
        navbar = soup.nav
        # 1.5 Blog, About Me라는 문구가 네비게이션 바에 있다.
        self.assertIn('Blog', navbar.text)
        self.assertIn('About me', navbar.text)

        logo_btn = navbar.find('a', text='Sua portfolio')  # 네비게이션 바에서 Sua portfolio문구를 가진 a요소를 찾아
        self.assertEqual(logo_btn.attrs['href'], '/')  # 그 요소의 href 값이 / 인지 확인

        home_btn = navbar.find('a', text='Home')
        self.assertEqual(home_btn.attrs['href'], '/')

        blog_btn = navbar.find('a', text='Blog')
        self.assertEqual(blog_btn.attrs['href'], '/blog/')

        about_me_btn = navbar.find('a', text='About me')
        self.assertEqual(about_me_btn.attrs['href'], '/about_me/')

    def test_post_list(self):
        # 포스트가 있는 경우
        self.assertEqual(Post.objects.count(), 3)

        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        self.navbar_test(soup)
        self.category_card_test(soup)

        main_area = soup.find('div', id='main-area')
        self.assertNotIn('아직 게시물이 없습니다', main_area.text)

        post_001_card = main_area.find('div', id='post-1')
        self.assertIn(self.post_001.title, post_001_card.text)
        self.assertIn(self.post_001.category.name, post_001_card.text)
        self.assertIn(self.post_001.author.username.upper(), post_001_card.text)
        self.assertIn(self.tag_hello.name, post_001_card.text)
        self.assertNotIn(self.tag_python.name, post_001_card.text)
        self.assertNotIn(self.tag_python_kor.name, post_001_card.text)

        post_002_card = main_area.find('div', id='post-2')
        self.assertIn(self.post_002.title, post_002_card.text)
        self.assertIn(self.post_002.category.name, post_002_card.text)
        self.assertIn(self.post_002.author.username.upper(), post_002_card.text)
        self.assertNotIn(self.tag_hello.name, post_002_card.text)
        self.assertNotIn(self.tag_python.name, post_002_card.text)
        self.assertNotIn(self.tag_python_kor.name, post_002_card.text)

        post_003_card = main_area.find('div', id='post-3')
        self.assertIn('미분류', post_003_card.text)
        self.assertIn(self.post_003.title, post_003_card.text)
        self.assertIn(self.post_003.author.username.upper(), post_003_card.text)
        self.assertNotIn(self.tag_hello.name, post_003_card.text)
        self.assertIn(self.tag_python.name, post_003_card.text)
        self.assertIn(self.tag_python_kor.name, post_003_card.text)

        self.assertIn(self.user_milan.username.upper(), main_area.text)
        self.assertIn(self.user_ain.username.upper(), main_area.text)

        # 포스트가 없는 경우
        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)
        response = self.client.get('/blog/')
        soup = BeautifulSoup(response.content, 'html.parser')
        main_area = soup.find('div', id='main-area')
        self.assertIn('아직 게시물이 없습니다.', main_area.text)

    def test_post_detail(self):
        # 1.2 그 포스트의 url은 '/blog/1/'이다.
        self.assertEqual(self.post_001.get_absolute_url(), '/blog/1/')

        # 2. 첫번째 포스트의 상세 페이지 테스트
        # 2.1 첫번째 포스트의 url로 접근하면 정상적으로 작동한다 (status_code, 200)
        response = self.client.get(self.post_001.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        # 2.2 포스트 목록 페이지와 똑같은 네비게이션 바가 있다
        self.navbar_test(soup)
        self.category_card_test(soup)
        # 2.3 첫 번째 포스트의 제목이 웹 브라우저 탭 타이틀에 들어있다
        self.assertIn(self.post_001.title, soup.title.text)
        # 2.4 첫번재 포스트의 제목이 포스트 영역에 있다
        main_area = soup.find('div', id='main-area')
        post_area = main_area.find('div', id='post-area')
        self.assertIn(self.post_001.title, post_area.text)
        self.assertIn(self.category_programming.name, post_area.text)
        # 2.5 첫번째 포스트의 작성자(author)가 포스트 영역에 있다.
        self.assertIn(self.user_milan.username.upper(), post_area.text)
        # 2.6 첫 번째 포스트의 내용(content)이 포스트 영역에 있다.
        self.assertIn(self.post_001.content, post_area.text)

        self.assertIn(self.tag_hello.name, post_area.text)
        self.assertNotIn(self.tag_python.name, post_area.text)
        self.assertNotIn(self.tag_python_kor.name, post_area.text)

        # comment area
        comments_area = soup.find('div', id='comment-area')
        comment_001_area = comments_area.find('div', id='comment-1')
        self.assertIn(self.comment_001.author.username, comment_001_area.text)
        self.assertIn(self.comment_001.content, comment_001_area.text)

    def test_create_post(self):
        response = self.client.get('/blog/create_post/')
        self.assertNotEqual(response.status_code, 200)

        # staff가 아닌 ain 유저가 로그인을 한다
        self.client.login(username='ain', password='somepassword')
        response = self.client.get('/blog/create_post/')
        self.assertNotEqual(response.status_code, 200)

        # staff 권한이 있는 milan 유저로 로그인한다
        self.client.login(username='milan', password='1234Arabbit')  # milan 유저로 로그인

        response = self.client.get('/blog/create_post/')
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        self.assertEqual('Create Post - Blog', soup.title.text)
        main_area = soup.find('div', id='main-area')
        self.assertIn('Create New Post', main_area.text)

        tag_str_input = main_area.find('input', id='id_tags_str')
        self.assertTrue(tag_str_input)

        self.client.post(
            '/blog/create_post/',
            {
                'title': 'Post Form 만들기',
                'content': 'Post form 페이지를 만들어봅니다.',
                'tags_str': 'new tag; 한글 태그, python'
            }
        )
        self.assertEqual(Post.objects.count(), 4)
        last_post = Post.objects.last()  # Post 레코드 중 맨 마지막 레코드를 가져와 last_post에 저장합니다.
        self.assertEqual(last_post.title, "Post Form 만들기")
        self.assertEqual(last_post.author.username, 'milan')

        self.assertEqual(last_post.tags.count(), 3)
        self.assertTrue(Tag.objects.get(name='new tag'))
        self.assertTrue(Tag.objects.get(name='한글 태그'))
        self.assertEqual(Tag.objects.count(), 5)

    def test_update_post(self):
        update_post_url = f'/blog/update_post/{self.post_003.pk}/'  # 수정할 포스트는 3번째 포스트

        # 로그인하지 않은 경우 - 접근 불가
        response = self.client.get(update_post_url)
        self.assertNotEqual(response.status_code, 200)  # 200이 아닌 다른 상태 코드가 나와야 함. 403이 나와야 함

        # 로그인은 했지만 작성자가 아닌 경우
        self.assertNotEqual(self.post_003.author, self.user_milan)
        self.client.login(
            username=self.user_milan.username,
            password='1234Arabbit'  # milan의 비밀번호로 로그인
        )
        response = self.client.get(update_post_url)
        self.assertEqual(response.status_code, 403)

        # 작성자가 접근하는 경우
        self.client.login(
            username=self.post_003.author.username,
            password='somepassword'  # 글쓴이 ain의 비밀번호로 로그인
        )
        response = self.client.get(update_post_url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        self.assertEqual('Edit Post - Blog', soup.title.text)
        main_area = soup.find('div', id='main-area')
        self.assertIn('Edit Post', main_area.text)

        tag_str_input = main_area.find('input', id='id_tags_str')
        self.assertTrue(tag_str_input)
        self.assertIn('파이썬 공부; python', tag_str_input.attrs['value'])

        response = self.client.post(
            update_post_url,
            {
                'title': '세번째 포스트를 수정했습니다.',
                'content': '세번째 포스트에는 무슨 내용이 들어가야 하지?',
                'category': self.category_programming.pk,
                'tags_str': '파이썬 공부; 한글 태그; some tag'
            },
            follow=True
        )
        soup = BeautifulSoup(response.content, 'html.parser')
        main_area = soup.find('div', id='main-area')
        self.assertIn('세번째 포스트를 수정했습니다.', main_area.text)
        self.assertIn('세번째 포스트에는 무슨 내용이 들어가야 하지?', main_area.text)
        self.assertIn(self.category_programming.name, main_area.text)
        self.assertIn('파이썬 공부', main_area.text)
        self.assertIn('한글 태그', main_area.text)
        self.assertIn('some tag', main_area.text)
        self.assertNotIn('python', main_area.text)

    def test_comment_form(self):
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(self.post_001.comment_set.count(), 1)

        # 로그인하지 않은 상태
        response = self.client.get(self.post_001.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        comment_area = soup.find('div', id='comment-area')
        self.assertIn('Log in and leave a comment', comment_area.text)
        self.assertFalse(comment_area.find('form', id='comment-form'))

        # 로그인한 상태
        self.client.login(username='milan', password='1234Arabbit')
        response = self.client.get(self.post_001.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        comment_area = soup.find('div', id='comment-area')
        self.assertNotIn('Log in and leave a comment', comment_area.text)

        comment_form = comment_area.find('form', id='comment-form')
        self.assertTrue(comment_form.find('textarea', id='id_content'))
        response = self.client.post(
            self.post_001.get_absolute_url() + 'new_comment/',
            {
                'content': "milan의 댓글입니다.",
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(self.post_001.comment_set.count(), 2)
        new_comment = Comment.objects.last()

        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertIn(new_comment.post.title, soup.title.text)

        comment_area = soup.find('div', id='comment-area')
        new_comment_div = comment_area.find('div', id=f'comment-{new_comment.pk}')
        self.assertIn('milan', new_comment_div.text)
        self.assertIn('milan의 댓글입니다.', new_comment_div.text)

    def test_comment_update(self):
        comment_by_trump = Comment.objects.create(  # 예시. 다른 사람이 작성한 댓글
            post=self.post_001,
            author=self.user_ain,
            content='ain의 댓글입니다.',
        )
        # 로그인 안 한 상태
        response = self.client.get(self.post_001.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        comment_area = soup.find('div', id='comment-area')
        self.assertFalse(comment_area.find('a', id='comment-1-update-btn'))  # 수정 버튼 보이지 X
        self.assertFalse(comment_area.find('a', id='comment-2-update-btn'))  # 수정 버튼 보이지 X

        # 로그인 한 상태 - 계정은 milan
        self.client.login(username='milan', password='1234Arabbit')
        response = self.client.get(self.post_001.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        comment_area = soup.find('div', id='comment-area')
        self.assertFalse(comment_area.find('a', id='comment-2-update-btn'))  # ain의 댓글은 수정 버튼 보이지 X
        comment_001_update_btn = comment_area.find('a', id='comment-1-update-btn')
        self.assertIn('edit', comment_001_update_btn.text)  # 본인 milan의 댓글은 수정버튼이 보여야 함
        self.assertEqual(comment_001_update_btn.attrs['href'], '/blog/update_comment/1/')  # 버튼에는 링크 경로가 담겨야 함

        response = self.client.get('/blog/update_comment/1/')  # edit 버튼을 클릭하면 해당 경로로 이동
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        self.assertEqual('Edit Comment - Blog', soup.title.text)  # 페이지의 이름은 Edit Comment - Blog
        update_comment_form = soup.find('form', id='comment-form')
        content_textarea = update_comment_form.find('textarea', id='id_content')
        self.assertIn(self.comment_001.content, content_textarea.text)

        response = self.client.post(
            f'/blog/update_comment/{self.comment_001.pk}/',
            {
                'content': "ain의 댓글을 수정합니다",
            },
            follow=True
        )

        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        comment_001_div = soup.find('div', id='comment-1')
        self.assertIn('ain의 댓글을 수정합니다', comment_001_div.text)
        self.assertIn('Updated:', comment_001_div.text)

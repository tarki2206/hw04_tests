import datetime

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Post, Group
from django import forms

User = get_user_model()


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.user_2 = User.objects.create_user(username='author_2')
        cls.group = Group.objects.create(
            title='group',
            slug='group_1'
        )
        cls.group_2 = Group.objects.create(
            title='group_2',
            slug='group_2'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post1 = Post.objects.create(
            text='test_text_2',
            author=self.user_2,
            group=self.group_2,
            pub_date=datetime.datetime.now()
        )

        self.post = Post.objects.create(
            text='test_text_1',
            author=self.user,
            group=self.group
        )

    def test_pages_uses_correct_template(self):
        html1 = 'create_post.html'
        templates_pages_names = {
            'posts/index.html': ('posts:main_posts', {}),
            'posts/group_list.html': ('posts:group_list',
                                      {'slug': self.group.slug}),
            'posts/profile.html': ('posts:profile',
                                   {'username': self.user}),
            'posts/post_detail.html': ('posts:post_detail',
                                       {'post_id': self.post.id}),
            'posts/create_post.html': ('posts:post_create', {}),
            f'posts/{html1}': ('posts:post_edit',
                               {'post_id': self.post.pk}),
        }
        for url_name, params in templates_pages_names.items():
            queryset, kwargs = params
            with self.subTest(url_name=url_name):
                response = self.authorized_client.get(
                    reverse(queryset, kwargs=kwargs))
                self.assertTemplateUsed(response, url_name)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:main_posts'))
        ex_context = ['user', 'page_obj']
        for name in ex_context:
            self.assertIn(name, response.context)
        post_context = response.context['page_obj'][0]
        self.assertEqual(post_context.text, self.post.text)

    def test_group_list_correct_context(self):
        response = (self.authorized_client.get
                    (reverse
                     ('posts:group_list',
                      kwargs={'slug': self.group.slug})))
        ex_context = ['user', 'group', 'page_obj']
        for name in ex_context:
            self.assertIn(name, response.context)
        post_context = response.context['page_obj'][0]
        self.assertEqual(post_context.author, self.post.author)
        self.assertEqual(post_context.text, self.post.text)
        self.assertEqual(post_context.group, self.post.group)

    def test_new_post_on_main_page(self):
        form_data = {
            'text': 'new_post',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data)
        new_post = Post.objects.latest('id')
        response = self.authorized_client.get(
            reverse('posts:main_posts'))
        last_post = response.context.get('page_obj')[0]
        self.assertEqual(last_post, new_post)

    def test_new_post_on_group_page(self):
        form_data = {
            'text': 'new_post',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data)
        new_post = Post.objects.latest('id')
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}))
        last_post = response.context.get('page_obj')[0]
        self.assertEqual(last_post, new_post)

    def test_new_post_on_profile_page(self):
        form_data = {
            'text': 'new_post',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data)
        new_post = Post.objects.latest('id')
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user}))
        last_post = response.context.get('page_obj')[0]
        self.assertEqual(last_post, new_post)

    def test_new_post_doesnt_show_on_dif_group(self):
        form_data = {
            'text': 'new_post',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data)
        new_post = Post.objects.latest('id')
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group_2.slug}))
        last_post = response.context.get('page_obj')[0]
        self.assertNotEqual(last_post, new_post)

    def test_profile_correct_context(self):
        response = self.authorized_client.get(reverse
                                              ('posts:profile',
                                               kwargs={'username': self.user}))
        ex_context = ['username', 'page_obj']
        for name in ex_context:
            self.assertIn(name, response.context)
            post_context = response.context['page_obj'][0]
            author = post_context.author
            self.assertEqual(author, self.post.author)

    def test_post_detail_correct_context(self):
        response = self.authorized_client.get(
            reverse
            ('posts:post_detail',
             kwargs={'post_id': self.post.id}))
        post_context = response.context['post']
        author = post_context.author
        text = post_context.text
        self.assertEqual(author, self.post.author)
        self.assertEqual(text, self.post.text)

    def test_create_post_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
            self.assertIsInstance(form_field, expected)

    def test_edit_post_show_correct_context(self):
        response = self.authorized_client.get(
            reverse
            ('posts:post_edit',
             kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
            self.assertIsInstance(form_field, expected)


POSTS_QUANTITY = 15
POSTS_QUANTITY_ON_FIRST_PAGE = 10
POST_QUANTITY_ON_SECOND_PAGE = 5


class PostViewPaginatorTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='group',
            slug='group_1'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        for i in range(POSTS_QUANTITY):
            self.post = Post.objects.create(
                text=f'test_text {i+1}',
                author=self.user,
                group=self.group
            )

    def test_paginator_main(self):
        response = self.authorized_client.get(reverse('posts:main_posts'))
        self.assertEqual(len(response.context['page_obj']),
                         POSTS_QUANTITY_ON_FIRST_PAGE)

    def test_paginator_main2(self):
        response = self.authorized_client.get(reverse
                                              ('posts:main_posts') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         POST_QUANTITY_ON_SECOND_PAGE)

    def test_paginator_group_list(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context['page_obj']),
                         POSTS_QUANTITY_ON_FIRST_PAGE)

    def test_paginator_group_list2(self):
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         POST_QUANTITY_ON_SECOND_PAGE)

    def test_paginator_profile(self):
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user}))
        self.assertEqual(len(response.context['page_obj']),
                         POSTS_QUANTITY_ON_FIRST_PAGE
                         )

    def test_paginator_profile2(self):
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         POST_QUANTITY_ON_SECOND_PAGE)

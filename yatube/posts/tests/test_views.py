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
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)

        self.post1 = Post.objects.create(
            text='test_text_2',
            author=self.user_2,
            group=self.group_2
        )

        self.post = Post.objects.create(
            text='test_text_1',
            author=self.user,
            group=self.group
        )

    def test_pages_uses_correct_template(self):
        html1 = 'create_post.html'
        templates_pages_names = {
            'posts/index.html': reverse('posts:main_posts'),
            'posts/group_list.html': reverse('posts:group_list',
                                             kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={'username': self.user}),
            'posts/post_detail.html': (reverse
                                       ('posts:post_detail',
                                        kwargs={'post_id': self.post.id})),
            'posts/create_post.html': reverse('posts:post_create'),
            f'posts/{html1}': reverse('posts:post_edit',
                                      kwargs={'post_id': self.post.pk}),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:main_posts'))
        first_object = response.context['page_obj'][0]
        text = first_object.text
        self.assertEqual(text, self.post.text)

    def test_group_list_correct_context(self):
        response = (self.authorized_client.get
                    (reverse
                     ('posts:group_list',
                      kwargs={'slug': self.group.slug})))
        first_object = response.context['page_obj'][0]
        author = first_object.author
        text = first_object.text
        group = first_object.group
        self.assertEqual(author, self.post.author)
        self.assertEqual(text, self.post.text)
        self.assertEqual(group, self.post.group)

    def test_profile_correct_context(self):
        response = self.authorized_client.get(reverse
                                              ('posts:profile',
                                               kwargs={'username': self.user}))
        first_object = response.context['page_obj'][0]
        author = first_object.author
        text = first_object.text
        self.assertEqual(author, self.post.author)
        self.assertEqual(text, self.post.text)

    def test_post_detail_correct_context(self):
        response = self.authorized_client.get(
            reverse
            ('posts:post_detail',
             kwargs={'post_id': self.post.id}))
        first_object = response.context['post']
        author = first_object.author
        text = first_object.text
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

    def test_new_post(self):
        form_data = {
            'text': 'new_post',
            'group': self.group.id
        }

        url_name_list = {
            reverse('posts:main_posts'): self.assertEqual,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): self.assertEqual,
            reverse('posts:profile',
                    kwargs={'username': self.user}): self.assertEqual,
            reverse('posts:group_list',
                    kwargs={'slug': self.group_2.slug}): self.assertNotEqual
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        new_post = Post.objects.latest('id')
        for address, method in url_name_list.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                last_post = response.context.get('page_obj')[0]
                method(last_post, new_post)


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

        for i in range(15):
            self.post = Post.objects.create(
                text=f'test_text {i+1}',
                author=self.user,
                group=self.group
            )

    def test_paginator_main(self):
        response = self.authorized_client.get(reverse('posts:main_posts'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_paginator_main2(self):
        response = self.authorized_client.get(reverse
                                              ('posts:main_posts') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 5)

    def test_paginator_group_list(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_paginator_group_list2(self):
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 5)

    def test_paginator_profile(self):
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_paginator_profile2(self):
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 5)

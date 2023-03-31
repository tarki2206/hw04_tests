from django.test import Client, TestCase
from django.urls import reverse
from ..models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Test group',
            slug='group_test'
        )
        cls.group_2 = Group.objects.create(
            title='Test group2',
            slug='group_test_2'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text='Post1',
            author=self.user,
            group=self.group)

    def test_create_post_form(self):

        post_count = Post.objects.all().count()
        form_data = {
            'text': 'Post2',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(
            Post.objects.all().count(),
            post_count + 1,
            "Post didn't save"
        )
        self.assertTrue(
            Post.objects.filter(
                text='Post1',
                group=self.group
            ).exists())
        self.assertTrue(
            Post.objects.filter(
                text='Post1',
                author=self.user
            ).exists())

    def test_edit_post_form(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'new post',
            'group': self.group_2.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True)
        modified_post = Post.objects.get(id=self.post.id)
        self.assertRedirects(response, reverse('posts:post_detail', args=(1,)))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertNotEqual(
            modified_post.text,
            self.post.text,
            "text didn't change"
        )
        self.assertNotEqual(
            modified_post.group,
            self.post.group,
            "Group didn't change"
        )
        self.assertEqual(modified_post.group.title,
                         'Test group2')

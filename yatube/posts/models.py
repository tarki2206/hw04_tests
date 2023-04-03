from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

SYMBOLS_LIMIT = 15


class Group(models.Model):
    title = models.CharField(verbose_name='title', max_length=200)
    slug = models.SlugField(verbose_name='slug', unique=True)
    description = models.TextField(verbose_name='description')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='content')
    pub_date = models.DateTimeField(verbose_name='date', auto_now_add=True)
    author = models.ForeignKey(User,
                               verbose_name='author',
                               on_delete=models.CASCADE,
                               related_name='posts')
    group = models.ForeignKey(Group,
                              verbose_name='group',
                              blank=True,
                              null=True,
                              on_delete=models.SET_NULL,
                              related_name='posts')

    def __str__(self):
        return self.text[:SYMBOLS_LIMIT]

    class Meta:
        ordering = ['-pub_date']

from django.db import models
from django.urls import reverse

from users.models import CustomUser

from words.utils import Slug


class Dictionary(models.Model):
    title = models.CharField('Название словаря', max_length=75)
    image = models.ImageField('Картинка', upload_to='dictionaries_images', null=True)
    slug = models.SlugField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'slug')
        verbose_name = 'Словарь'
        verbose_name_plural = 'Словари'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('words:show_dictionary', kwargs={'dict_slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = Slug(self.title).slug
        super().save(*args, **kwargs)


class PairWord(models.Model):
    original = models.CharField(max_length=150)
    translation = models.CharField(max_length=150)
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('dictionary', 'original')

    def __str__(self):
        return f"{self.original} - {self.translation}"


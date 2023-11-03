from datetime import datetime
from random import shuffle

from django.utils import timezone
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse

from users.models import CustomUser
from words.utils import Slug


class Dictionary(models.Model):
    title = models.CharField('Название словаря', max_length=75)
    image = models.ImageField('Картинка', upload_to='dictionaries_images', null=True)
    slug = models.SlugField(max_length=80)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
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
        if not self.created_at:
            self.created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.slug = Slug(self.title).slug
        self.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        super().save(*args, **kwargs)


class PairWord(models.Model):
    original = models.CharField(max_length=150)
    translation = models.CharField(max_length=150)
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('dictionary', 'original')

    def __str__(self):
        return f"{self.original} - {self.translation}"


class UserLearningData(models.Model):
    dictionary = models.ForeignKey(Dictionary, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    session_active = models.BooleanField(default=False)
    level = models.IntegerField(default=1)
    start_index = models.IntegerField(default=0)
    end_index = models.IntegerField(default=5)
    step = models.IntegerField(default=5)
    stop_learning = models.IntegerField(default=5)
    point = models.IntegerField(default=0)
    next_level_point = models.IntegerField(default=5)
    current_word_index = models.IntegerField(default=0)
    created_at = models.DateTimeField()

    def __str__(self):
        return f'{self.dictionary} | {self.user} | {self.session_active} | {self.level}'

    class Meta:
        unique_together = ('dictionary', 'user')

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        super().save(*args, **kwargs)

    def check_days(self):
        now = datetime.now()

        match self.created_at:
            case str(created) if '+' not in created:
                created = datetime.strptime(self.created_at, '%Y-%m-%d %H:%M:%S')
            case _:
                created = datetime.strptime(str(self.created_at)[:-6], '%Y-%m-%d %H:%M:%S')

        return (now - created).days

    def reset_session(self):
        self.level = self._meta.get_field('level').get_default()
        self.start_index = self._meta.get_field('start_index').get_default()
        self.end_index = self._meta.get_field('end_index').get_default()
        self.step = self._meta.get_field('step').get_default()
        self.stop_learning = self._meta.get_field('stop_learning').get_default()
        self.point = self._meta.get_field('point').get_default()
        self.next_level_point = self._meta.get_field('next_level_point').get_default()
        self.current_word_index = self._meta.get_field('current_word_index').get_default()
        self.created_at = None
        self.session_active = self._meta.get_field('session_active').get_default()
        self.save()

    def __check_and_reset_learning_data(self, db_words: list[dict]) -> None:
        if self.start_index > len(db_words) - 1:
            self.level += 1
            self.start_index = 0
            self.end_index = self.step
            self.save()

    def __filter_study_words(self, study_words: list[dict]) -> list[dict]:
        return list(filter(lambda pair: pair['point'] < self.next_level_point, study_words))

    def __generate_study_words(self, db_words: QuerySet) -> list[dict]:
        study_words = [{'pair': [pair.original, pair.translation], 'point': self.point}
                       for pair in db_words[self.start_index:self.end_index]]

        shuffle(study_words)

        return study_words

    def check_current_word_index(self, study_words):
        if self.current_word_index + 1 > len(study_words):
            self.current_word_index = 0

    def update_current_word_index(self):
        self.current_word_index += 1
        self.save()

    def update_learning_data(self, study_words: list[dict]):
        if self.level > self.stop_learning:
            self.reset_session()
            return
        if study_words:
            study_words = self.__filter_study_words(study_words)

        else:
            db_words = PairWord.objects.filter(dictionary=self.dictionary).order_by('id')

            # проверяем start_index
            self.__check_and_reset_learning_data(db_words)

            # Генерируем новый список слов
            study_words = self.__generate_study_words(db_words)

            # обновляем star/end/current_index - index
            self.current_word_index = 0
            self.start_index = self.end_index
            self.end_index = self.end_index + self.step

        self.check_current_word_index(study_words)
        self.save()

        return study_words

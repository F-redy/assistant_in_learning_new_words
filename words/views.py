from random import shuffle

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from common.views import DataMixin

from .forms import (AddDictionaryForm, AddPairWordForm, ImportWordsForm,
                    PairWordForm, RepeatWordForm)
from .models import Dictionary, PairWord, UserLearningData
from .utils import (Slug, get_delete_and_updated_words, get_existing_originals,
                    get_sep, get_unique_pairs)


class AddDictionaryView(DataMixin, SuccessMessageMixin, CreateView):
    form_class = AddDictionaryForm
    template_name = 'words/add_dictionary.html'
    title = "New Dictionary"

    def form_valid(self, form):
        user = self.request.user

        slug = Slug(form.cleaned_data['title']).slug
        existing_dictionary = Dictionary.objects.filter(user=user, slug=slug).first()
        if existing_dictionary:
            messages.error(self.request, 'Dictionary with this name already exists.')
            return redirect(reverse('words:add_dictionary'))

        dictionary = form.save(commit=False)
        dictionary.user = user

        dictionary.save()

        return HttpResponseRedirect(reverse('words:add_new_words'))


class AddPairWordView(DataMixin, CreateView):
    form_class = AddPairWordForm
    template_name = 'words/add_new_pair_words.html'
    title = 'Add New Pairs Words'

    def form_valid(self, form):
        dictionary_id = form.data.get('dictionary')
        dictionary = Dictionary.objects.get(id=dictionary_id)

        original_words = form.data.getlist('original_word')
        translation_words = form.data.getlist('translation_word')

        pair_objects = []
        for original, translation in zip(original_words, translation_words):
            original, translation = original.strip().lower(), translation.strip().lower()
            pair_objects.append(PairWord(original=original, translation=translation, dictionary=dictionary))

        PairWord.objects.bulk_create(pair_objects)
        dictionary.save()

        return HttpResponseRedirect(reverse('words:show_dictionary', kwargs={'dict_slug': dictionary.slug}))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user

        return kwargs


class ImportWordsView(DataMixin, CreateView):
    form_class = ImportWordsForm
    template_name = 'words/import_words.html'
    title = 'Import New Pairs Words'

    def form_valid(self, form):
        id_dictionary = form.data.get('dictionary')
        dictionary = Dictionary.objects.get(id=id_dictionary)

        text = form.cleaned_data.get('text')

        if text:
            sep = get_sep(form)
            db_words = PairWord.objects.filter(dictionary_id=id_dictionary)
            existing_originals = get_existing_originals(db_words)
            words_for_db = get_unique_pairs(text, existing_originals, sep, dictionary, PairWord)

            if words_for_db:
                PairWord.objects.bulk_create(words_for_db)
                dictionary.save()

        return HttpResponseRedirect(reverse('words:show_dictionary', kwargs={'dict_slug': dictionary.slug}))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user

        return kwargs


class ShowAllDictionaryUserView(DataMixin, ListView):
    model = Dictionary
    template_name = 'words/show_all_dictionaries_user.html'
    title = 'Home'

    def get_queryset(self):
        dictionaries = Dictionary.objects.filter(user_id=self.request.user.pk).order_by('-updated_at')
        dictionaries = dictionaries.annotate(count_words=Count('pairword'))
        return dictionaries


class ShowDictionaryView(DetailView):
    model = Dictionary
    template_name = 'words/show_dictionary.html'
    slug_url_kwarg = 'dict_slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dict_slug'] = self.kwargs['dict_slug']
        context['title'] = self.object.title
        word_list = PairWord.objects.filter(dictionary=self.object).select_related('dictionary').order_by('-id')

        context['word_list'] = word_list
        context['word_data'] = [{'original': word.original, 'translation': word.translation} for word in word_list]
        return context

    def get_queryset(self):
        dictionary = Dictionary.objects.filter(user_id=self.request.user.pk, slug=self.kwargs[self.slug_url_kwarg])
        dictionary = dictionary.annotate(count_words=Count('pairword'))

        return dictionary


class UpdateDictionaryView(SuccessMessageMixin, UpdateView):
    model = Dictionary
    template_name = 'words/update_dictionary.html'
    slug_url_kwarg = 'dict_slug'
    context_object_name = 'dictionary'
    fields = ['title']

    def get_queryset(self):
        return Dictionary.objects.filter(slug=self.kwargs['dict_slug'], user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dictionary = self.object
        words_to_change = PairWord.objects.filter(dictionary=dictionary).order_by('-id')
        context['title'] = dictionary.title
        context['count_words'] = words_to_change.count()
        PairWordFormSet = inlineformset_factory(Dictionary, PairWord, form=PairWordForm, extra=0)
        context['formset'] = PairWordFormSet(instance=dictionary, queryset=words_to_change)

        return context

    def post(self, request, *args, **kwargs):
        changed_title = self.request.POST.get('title').strip()
        slug = Slug(changed_title).slug

        dictionary = self.get_object()
        words_to_change = PairWord.objects.filter(dictionary=dictionary)
        PairWordFormSet = inlineformset_factory(Dictionary, PairWord, form=PairWordForm, extra=0)
        formset = PairWordFormSet(request.POST, instance=dictionary, queryset=words_to_change)

        if formset.is_valid():
            words_to_delete, updated_words = get_delete_and_updated_words(formset, PairWord, dictionary)

            if words_to_delete:
                # Выполняем удаление слов
                PairWord.objects.filter(id__in=words_to_delete).delete()

            if updated_words:
                PairWord.objects.bulk_update(updated_words, ['original', 'translation'])

            if kwargs['dict_slug'] != slug:
                dictionary.title = changed_title

            dictionary.save()
            messages.success(request, f'the {dictionary.title} has been changed')
        return redirect('words:update_dictionary', dict_slug=slug)


def delete_dictionary(request, dict_slug):
    dictionary = get_object_or_404(Dictionary, slug=dict_slug, user=request.user)
    if dictionary:
        dictionary.delete()

        return redirect('words:show_dictionaries')


class RepeatWordsView(SuccessMessageMixin, DetailView):
    model = Dictionary
    template_name = 'words/study_words.html'
    slug_url_kwarg = 'dict_slug'

    def get_context(self, **kwargs):
        title = ' '.join(kwargs["dict_slug"].split('-')).title()
        form = RepeatWordForm()
        reset_url = kwargs.get('reset_url')
        current_word_index = kwargs['request'].session.get('current_word_index') or 0
        custom_messages = {
            'translation': kwargs['translation'],
            'original': kwargs['original'],
        }

        if kwargs.get('user_answer'):
            custom_messages['error_answer'] = kwargs['user_answer'] != kwargs.get('original')
            custom_messages['user_answer'] = kwargs.get('user_answer')
            kwargs['request'].session['current_word_index'] = current_word_index + 1

            if kwargs['user_answer'] != kwargs.get('original'):
                error_words = kwargs['request'].session.get('error_words') or list()
                error_words.append((kwargs['original'], kwargs['translation']))
                kwargs['request'].session['error_words'] = error_words
        length = kwargs["request"].session.get("words")
        if length:
            length = len(length)
        context = {
            'title': f'Repeat {title} | {current_word_index + 1}/{length}',
            'form': form,
            'reset_url': reset_url,
            'custom_messages': custom_messages,
        }

        return context

    @staticmethod
    def check_dict_session(request, **kwargs):
        if kwargs['dict_slug'] != request.session.get('dict_session'):
            request.session['dict_session'] = kwargs['dict_slug']

    def get_pair(self, request, **kwargs):
        self.check_dict_session(request, **kwargs)

        words = request.session.get('words')
        current_word_index = request.session.get('current_word_index') or 0

        if words is None:
            request.session['error_words'] = None
            words = PairWord.objects.filter(dictionary__slug=kwargs['dict_slug'])
            words = [(pair.original, pair.translation) for pair in words]
            shuffle(words)

        if current_word_index < len(words) - 1:
            original = words[current_word_index][0]
            translation = words[current_word_index][1]
            request.session['words'] = words
            return original, translation

    def get(self, request, *args, **kwargs):
        pair = self.get_pair(request, **kwargs)

        if pair:
            context = self.get_context(
                **{
                    'request': request,
                    'dict_slug': kwargs["dict_slug"],
                    'translation': pair[1],
                    'original': pair[0],
                }
            )

            return render(request, 'words/study_words.html', context=context)

        request.session['current_word_index'] = 0
        request.session['words'] = None
        return redirect('words:congratulations')

    def post(self, request, *args, **kwargs):
        user_answer = self.request.POST.get('user_answer')
        pair = self.get_pair(request, **kwargs)

        if pair:
            context = self.get_context(
                **{
                    'request': request,
                    'dict_slug': kwargs["dict_slug"],
                    'translation': pair[1],
                    'original': pair[0],
                    'user_answer': user_answer,
                }
            )
            return render(request, 'words/user_answer.html', context=context)

        request.session['current_word_index'] = 0
        request.session['words'] = None
        return redirect('words:congratulations')


class StudyWordsView(DetailView):
    model = Dictionary
    template_name = 'words/study_words.html'
    slug_url_kwarg = 'dict_slug'

    def __init__(self):
        super().__init__()
        self.game_session = None
        self.study_service = None
        self.custom_messages = {}

    def get(self, request, *args, **kwargs):
        self.get_study_data(request, *args, **kwargs)

        if self.study_service.study_words and self.custom_messages:
            context = self.get_common_context(kwargs['dict_slug'])

            return render(request, 'words/study_words.html', context=context)

        self.game_session.reset_data_active_session()
        return redirect(reverse('words:repeat_words', kwargs={'dict_slug': kwargs['dict_slug']}))

    def post(self, request, *args, **kwargs):
        self.get_study_data(request, *args, **kwargs)

        if self.study_service.study_words and self.custom_messages:
            context = self.get_common_context(kwargs['dict_slug'])
            self.game_session.update_current_word_index()

            return render(request, 'words/user_answer.html', context=context)

        self.game_session.reset_data_active_session()
        return redirect(reverse('words:repeat_words', kwargs={'dict_slug': kwargs['dict_slug']}))

    def get_study_data(self, request, *args, **kwargs):
        self.game_session = SessionService(request, kwargs['dict_slug'])
        self.study_service = StudyWordsService(request, self.game_session)
        self.custom_messages = CustomMessagesService(
            request, self.game_session.active_session.current_word_index, self.study_service.study_words
        ).custom_messages

    def get_study_words_url(self):
        return str(reverse_lazy('words:study_words', kwargs={'dict_slug': self.kwargs["dict_slug"]}))

    def get_common_context(self, dictionary_slug):

        title = ' '.join(dictionary_slug.split('-')).title()
        context = {
            'title': f'Study: {title} | level: {self.game_session.active_session.level}',
            'form': RepeatWordForm(),
            'dict_slug': self.kwargs['dict_slug'],
            'user_answer_url': self.get_study_words_url(),
            'custom_messages': self.custom_messages,
        }
        return context


def show_error_words(request):
    context = {'title': 'Error Words', 'error_words': request.session.get('error_words')}
    return render(request, 'words/error_words.html', context)


def reset(request):
    request.session['current_word_index'] = None
    request.session['original'] = None
    request.session['translation'] = None

    return render(request, 'words/finished.html', {'title': 'Congratulations'})

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

    def _process_word(self, request, **kwargs):
        words = PairWord.objects.filter(dictionary__slug=kwargs['dict_slug']).order_by('id')
        current_word_index = request.session.get('current_word_index', 0)

        if current_word_index < len(words):
            original = words[current_word_index].original
            translation = words[current_word_index].translation

            request.session['original'] = original
            request.session['translation'] = translation

            title = ' '.join(self.kwargs["dict_slug"].split('-')).title()
            form = RepeatWordForm()
            reset_url = reverse('words:repeat_words', kwargs={'dict_slug': kwargs["dict_slug"]})

            context = {'translation': translation,
                       'title': f'Repeat {title}',
                       'form': form,
                       'reset_url': reset_url}

            return render(request, self.template_name, context)
        else:
            # Все слова уже отгаданы или список слов пуст
            request.session['current_word_index'] = 0
            request.session['original'] = ''
            request.session['translation'] = ''
            return redirect('words:congratulations')

    def get(self, request, *args, **kwargs):
        request.session['current_word_index'] = 0
        request.session['error_words'] = []
        return self._process_word(request, **kwargs)

    def post(self, request, *args, **kwargs):
        user_answer = self.request.POST.get('user_answer', '')
        get_original = request.session.get('original')
        get_translation = request.session.get('translation')

        request.session['current_word_index'] += 1

        if user_answer == get_original:
            messages.info(request, f'{get_original}')
            messages.success(request, f'{user_answer}')

        else:
            request.session.get('error_words', []).append((get_original, get_translation))
            messages.info(request, f'{get_translation}')
            messages.error(request, f'{user_answer}')
            messages.success(request, f'{get_original}')

        return self._process_word(request, **kwargs)


class StudyWordsView(DetailView):
    model = Dictionary
    template_name = 'words/study_words.html'
    slug_url_kwarg = 'dict_slug'

    def __init__(self):
        super().__init__()
        self.active_session = None
        self.study_words = None
        self.current_word_index = None
        self.custom_messages = {}

    def get_study_words_url(self):
        return str(reverse_lazy('words:study_words', kwargs={'dict_slug': self.kwargs["dict_slug"]}))

    def set_or_create_active_session(self):
        user = self.request.user
        dictionary = Dictionary.objects.filter(slug=self.kwargs['dict_slug'], user=user).first()
        active_session, _ = UserLearningData.objects.get_or_create(
            dictionary=dictionary, user=user
        )
        if not active_session.session_active:
            active_session.session_active = True
        if active_session.check_days() or active_session.level > active_session.stop_learning:
            active_session.reset()

        self.active_session = active_session
        self.current_word_index = active_session.current_word_index

    # def get(self, request, *args, **kwargs):
    #     active_session = self.get_or_create_active_session(request)
    #     if active_session.dictionary.slug != request.session.get('dictionary_session'):
    #         request.session['study_words'] = None
    #
    #     study_words = active_session.update_learning_data(study_words=self.request.session.get('study_words'))
    #
    #     if study_words:
    #         title = ' '.join(kwargs["dict_slug"].split('-')).title()
    #
    #         context = {'translation': study_words[active_session.current_word_index]['pair'][1],
    #                    'title': f'Study {title}',
    #                    'form': RepeatWordForm(),
    #                    'dict_slug': self.kwargs['dict_slug'],
    #                    'come_back_url': self.get_study_words_url(),
    #                    }
    #
    #         self.request.session['study_words'] = study_words
    #         self.request.session['dictionary_session'] = self.kwargs['dict_slug']
    #
    #         return render(request, 'words/study_words.html', context=context)
    #     self.request.session['study_words'] = None
    #
    #     return redirect(reverse('words:repeat_words', kwargs={'dict_slug': kwargs['dict_slug']}))
    #
    # def post(self, request, *args, **kwargs):
    #     active_session = self.get_or_create_active_session(request)
    #     study_words = active_session.update_learning_data(
    #         study_words=self.request.session.get('study_words')
    #     )
    #     custom_messages = {}
    #
    #     user_answer = self.request.POST.get('user_answer', '').strip().lower()
    #
    #     original = study_words[active_session.current_word_index]['pair'][0]
    #     point = study_words[active_session.current_word_index]['point']
    #
    #     if user_answer == original:
    #         point += 1
    #         if point > 4:
    #             point_message = 'pair goes next level'
    #         else:
    #             point_message = f'point: {point}'
    #     else:
    #         point -= 1
    #         point_message = f'point: {point}'
    #         custom_messages['error_answer'] = True
    #
    #     custom_messages['translation'] = study_words[active_session.current_word_index]['pair'][1]
    #     custom_messages['original'] = original
    #     custom_messages['point'] = point_message
    #     custom_messages['user_answer'] = user_answer
    #
    #     study_words[active_session.current_word_index]['point'] = point
    #
    #     title = ' '.join(self.kwargs["dict_slug"].split('-')).title()
    #
    #     context = {
    #
    #         'title': f'Study: {title}',
    #         'form': RepeatWordForm(),
    #         'dict_slug': self.kwargs['dict_slug'],
    #         'user_answer_url': self.get_study_words_url(),
    #         'custom_messages': custom_messages,
    #     }
    #
    #     self.request.session['study_words'] = study_words
    #     active_session.update_current_word_index()
    #
    #     return render(request, 'words/user_answer.html', context=context)

    def get(self, request, *args, **kwargs):
        self.set_or_create_active_session()
        self.check_session_and_reset_data()

        self.study_words = self.active_session.update_learning_data(self.request.session.get('study_words'))

        if self.study_words:
            self.set_custom_messages()
            context = self.get_common_context(kwargs['dict_slug'])
            print(f'get: {context = } {self.active_session.current_word_index = }')
            return render(request, 'words/study_words.html', context=context)

        return redirect(reverse('words:repeat_words', kwargs={'dict_slug': kwargs['dict_slug']}))

    def post(self, request, *args, **kwargs):
        self.set_or_create_active_session()
        self.check_session_and_reset_data()

        self.study_words = self.active_session.update_learning_data(self.request.session.get('study_words'))

        self.set_custom_messages(check_user_answer=True)
        self.active_session.update_current_word_index()

        context = self.get_common_context(kwargs['dict_slug'])
        print(f'post: {context = } {self.active_session.current_word_index = }')

        return render(request, 'words/user_answer.html', context=context)

    def check_session_and_reset_data(self):
        if self.active_session.dictionary.slug != self.request.session.get('dictionary_session'):
            self.request.session['study_words'] = None
            self.request.session['dictionary_session'] = None

    def set_custom_messages(self, check_user_answer=False):
        self.custom_messages = {}
        point_message = ''
        user_answer = ''

        original, translation = self.study_words[self.current_word_index]['pair']
        point = self.study_words[self.current_word_index]['point']

        if check_user_answer:
            user_answer = self.request.POST.get('user_answer', '').strip().lower()

            if user_answer == original:
                point += 1
                if point > 4:
                    point_message = 'pair goes next level'
                else:
                    point_message = f'point: {point}'
            else:
                point -= 1
                point_message = f'point: {point}'
                self.custom_messages['error_answer'] = True

        self.study_words[self.current_word_index]['point'] = point

        self.custom_messages.update({
            'translation': translation,
            'original': original,
            'point': point_message,
            'user_answer': user_answer,
        })

        self.study_words = self.active_session.update_learning_data(study_words=self.study_words)
        self.request.session['study_words'] = self.study_words

    def get_common_context(self, dictionary_slug):

        title = ' '.join(dictionary_slug.split('-')).title()
        context = {
            'title': title,
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

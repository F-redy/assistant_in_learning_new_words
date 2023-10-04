from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from common.views import DataMixin

from .forms import AddDictionaryForm, AddPairWordForm, ImportWordsForm, RepeatWordForm
from .models import Dictionary, PairWord
from .utils import get_sep, get_existing_originals, get_unique_pairs


class AddDictionaryView(DataMixin, CreateView):
    form_class = AddDictionaryForm
    template_name = 'words/add_dictionary.html'
    success_url = reverse_lazy('words:add_new_words')
    title = "New Dictionary"

    def form_valid(self, form):
        user = self.request.user

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

        # Добавление слов
        original_words = form.data.getlist('original_word')
        translation_words = form.data.getlist('translation_word')

        pair_objects = []
        for original, translation in zip(original_words, translation_words):
            pair_objects.append(PairWord(original=original, translation=translation, dictionary=dictionary))

        PairWord.objects.bulk_create(pair_objects)

        return HttpResponseRedirect(reverse('words:show_dictionary', kwargs={'dict_slug': dictionary.slug}))


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
            words_for_db = get_unique_pairs(text, existing_originals, sep, id_dictionary, PairWord)

            if words_for_db:
                PairWord.objects.bulk_create(words_for_db)

        return HttpResponseRedirect(reverse('words:show_dictionary', kwargs={'dict_slug': dictionary.slug}))
        # if not form.cleaned_data.get('custom_sep'):
        #     sep = form.cleaned_data.get('sep_choice')
        # else:
        #     sep = form.cleaned_data.get('custom_sep')

        # words = []

        # if text:
        #     db_words = PairWord.objects.filter(dictionary_id=id_dictionary)
        #     existing_originals = set(db_word.original for db_word in db_words)

        # for pair in text.split('\n'):
        #     try:
        #         original, translation = pair.split(sep)
        #         if original not in existing_originals:
        #             words.append(PairWord(original=original, translation=translation, dictionary=dictionary))
        #     except ValueError:
        #         words.append(PairWord(original=pair, translation='', dictionary=dictionary))

        # if words:
        #     PairWord.objects.bulk_create(words)
        #
        # return HttpResponseRedirect(reverse('words:show_dictionary', kwargs={'dict_slug': dictionary.slug}))


class ShowAllDictionaryUserView(DataMixin, ListView):
    model = Dictionary
    template_name = 'words/show_all_dictionaries_user.html'
    title = 'All Your Dictionaries'

    def get_queryset(self):
        dictionaries = Dictionary.objects.filter(user_id=self.request.user.pk)

        dictionaries = dictionaries.annotate(count_words=Count('pairword'))
        return dictionaries


class ShowDictionaryView(DetailView):
    model = Dictionary
    template_name = 'words/show_dictionary.html'
    slug_url_kwarg = 'dict_slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs['dict_slug']
        context['dict_slug'] = slug
        context['title'] = self.object.title
        context['word_list'] = PairWord.objects.filter(dictionary=self.object).select_related('dictionary')
        return context


class RepeatWordsView(SuccessMessageMixin, DetailView):
    model = Dictionary
    template_name = 'words/repeat_words.html'
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
            context = {'translation': translation, 'title': f'Repeat {title}', 'form': form}

            return render(request, 'words/repeat_words.html', context)
        else:
            # Все слова уже отгаданы или список слов пуст
            request.session['current_word_index'] = 0
            request.session['original'] = ''
            request.session['translation'] = ''
            return redirect('words:congratulations')

    def get(self, request, *args, **kwargs):
        request.session['current_word_index'] = 0
        request.session['error_words'] = []
        messages.success(request, 'Go Go Go')
        return self._process_word(request, **kwargs)

    def post(self, request, *args, **kwargs):
        user_answer = self.request.POST.get('user_answer', '')
        get_original = request.session.get('original')
        get_translation = request.session.get('translation')

        request.session['current_word_index'] += 1

        if user_answer == get_original:
            messages.success(request, 'Great! You are right!')
        else:
            request.session.get('error_words', []).append((get_original, get_translation))
            messages.error(request, f'Oops.. Error. {get_translation} = {get_original}')

        return self._process_word(request, **kwargs)


def show_error_words(request):
    context = {'title': 'Error Words', 'error_words': request.session['error_words']}
    return render(request, 'words/error_words.html', context)


def reset(request):
    request.session['current_word_index'] = None
    request.session['original'] = None
    request.session['translation'] = None

    return render(request, 'words/finished.html', {'title': 'Congratulations'})

from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views.generic import DetailView, ListView, CreateView

from common.views import DataMixin
from .models import Dictionary, PairWord
from .forms import AddDictionaryForm, AddPairWordForm, ImportWordsForm


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
        dictionary = Dictionary.objects.get(id=dictionary_id).select_related('user')

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
        dictionary = Dictionary.objects.get(id=id_dictionary).select_related('user')

        text = form.cleaned_data.get('text')

        if not form.cleaned_data.get('custom_sep'):
            sep = form.cleaned_data.get('sep_choice')
        else:
            sep = form.cleaned_data.get('custom_sep')

        words = []

        if text:
            for pair in text.split('\n'):
                try:
                    original, translation = pair.split(sep)
                    words.append(PairWord(original=original, translation=translation, dictionary=dictionary))
                except ValueError:
                    words.append(PairWord(original=pair, translation='', dictionary=dictionary))

        if words:
            PairWord.objects.bulk_create(words)

        return HttpResponseRedirect(reverse('words:show_dictionary', kwargs={'dict_slug': dictionary.slug}))


class ShowAllDictionaryUserView(DataMixin, ListView):
    model = Dictionary
    template_name = 'words/show_all_dictionaries_user.html'
    title = 'All Your Dictionaries'

    def get_queryset(self):
        return Dictionary.objects.filter(user_id=self.request.user.pk)


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

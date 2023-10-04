from django.contrib.auth.decorators import login_required
from django.urls import path

from words.views import (AddDictionaryView, AddPairWordView, ImportWordsView,
                         RepeatWordsView, ShowAllDictionaryUserView,
                         ShowDictionaryView, reset, show_error_words)

app_name = 'words'

urlpatterns = [
    path('add-new-dictionary/', login_required(AddDictionaryView.as_view()), name='add_dictionary'),
    path('add-new-words/', login_required(AddPairWordView.as_view()), name='add_new_words'),
    path('import-new-words/', login_required(ImportWordsView.as_view()), name='import_new_words'),

    path('show-dictionaries/', ShowAllDictionaryUserView.as_view(), name='show_dictionaries'),
    path('show-dictionary/<slug:dict_slug>', ShowDictionaryView.as_view(), name='show_dictionary'),

    path('repeat-words/<slug:dict_slug>', RepeatWordsView.as_view(), name='repeat_words'),

    path('congratulations/', reset, name='congratulations'),
    path('error-words/', show_error_words, name='error_words'),
]

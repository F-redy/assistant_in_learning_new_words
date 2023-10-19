from django.contrib.auth.decorators import login_required
from django.urls import path

from words.views import (AddDictionaryView, AddPairWordView, ImportWordsView,
                         RepeatWordsView, ShowAllDictionaryUserView,
                         ShowDictionaryView, StudyWordsView,
                         UpdateDictionaryView, delete_dictionary, reset,
                         show_error_words)

app_name = 'words'

urlpatterns = [
    path('add-new-dictionary/', login_required(AddDictionaryView.as_view()), name='add_dictionary'),
    path('add-new-words/', login_required(AddPairWordView.as_view()), name='add_new_words'),
    path('import-new-words/', login_required(ImportWordsView.as_view()), name='import_new_words'),

    path('', ShowAllDictionaryUserView.as_view(), name='show_dictionaries'),
    path('show-dictionary/<slug:dict_slug>', ShowDictionaryView.as_view(), name='show_dictionary'),
    path('update-dictionary/<slug:dict_slug>', UpdateDictionaryView.as_view(), name='update_dictionary'),
    path('delete-dictionary/<slug:dict_slug>', delete_dictionary, name='delete_dictionary'),

    path('study-words/<slug:dict_slug>', StudyWordsView.as_view(), name='study_words'),
    path('repeat-words/<slug:dict_slug>', RepeatWordsView.as_view(), name='repeat_words'),

    path('congratulations/', reset, name='congratulations'),
    path('error-words/', show_error_words, name='error_words'),
]

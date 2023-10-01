from django.contrib.auth.decorators import login_required
from django.urls import path

from words.views import (AddDictionaryView, AddPairWordView, ShowDictionaryView, ShowAllDictionaryUserView,
                         ImportWordsView)

app_name = 'words'

urlpatterns = [
    path('add-new-dictionary/', login_required(AddDictionaryView.as_view()), name='add_dictionary'),
    path('add-new-words/', login_required(AddPairWordView.as_view()), name='add_new_words'),
    path('import-new-words/', login_required(ImportWordsView.as_view()), name='import_new_words'),
    path('show-dictionary/<slug:dict_slug>', ShowDictionaryView.as_view(), name='show_dictionary'),
    path('show-dictionary/', ShowAllDictionaryUserView.as_view(), name='show_dictionaries'),
]

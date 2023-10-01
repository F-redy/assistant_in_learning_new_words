from django import forms

from .models import Dictionary, PairWord


class AddDictionaryForm(forms.ModelForm):
    title = forms.CharField(max_length=150,
                            widget=forms.TextInput(attrs={'placeholder': 'Enter the name of the dictionary',
                                                          'style': 'width: 300px;'}))

    class Meta:
        model = Dictionary
        fields = ('title',)


class AddPairWordForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dictionary'].empty_label = 'No dictionary selected'

    class Meta:
        model = PairWord
        fields = ('original_word', 'translation_word', 'dictionary')

    original_word = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'original word'}))
    translation_word = forms.CharField(max_length=150,
                                       widget=forms.TextInput(attrs={'placeholder': 'translation word'}))


class ImportWordsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dictionary'].empty_label = 'No dictionary selected'

    text = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Original 1 - Translation 1\n'
                                                                       'Original 2 - Translation 2\n'
                                                                       'Original 3 - Translation 3\n'
                                                                       '...'
                                                        }))

    sep_choice = forms.ChoiceField(
        choices=((' - ', 'Default: - '), ('Custom', 'Custom separator')),
        initial=' - ',
        widget=forms.RadioSelect(),
    )
    custom_sep = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter custom separator'}),
    )

    class Meta:
        model = PairWord
        fields = ('dictionary', 'text', 'sep_choice', 'custom_sep')

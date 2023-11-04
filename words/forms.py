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
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dictionary'].empty_label = 'No dictionary selected'
        self.fields['dictionary'].queryset = Dictionary.objects.filter(user=user)

    original_word = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'original word', 'class': 'input-word'}))

    translation_word = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'translation word', 'class': 'input-word'}))

    class Meta:
        model = PairWord
        fields = ('original_word', 'translation_word', 'dictionary')


class ImportWordsForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dictionary'].empty_label = 'No dictionary selected'
        self.fields['dictionary'].queryset = Dictionary.objects.filter(user=user)

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


class RepeatWordForm(forms.Form):
    user_answer = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'type': 'text',
                'class': 'user-answer',
                'autofocus': True,
                'placeholder': 'Enter your answer...',
            }),
        label='your answer',
        max_length=100
    )


class PairWordForm(forms.ModelForm):
    original = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'word'}),
        required=True
    )

    translation = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'word'}),
        required=True
    )

    delete = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'delete-checkbox'})
    )

    class Meta:
        model = PairWord
        fields = ['original', 'translation']

import re

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

cyrillic_to_latin = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y',
    'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
    'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': 'ie', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu',
    'я': 'ya', 'і': 'i', 'ї': 'i', 'є': 'ie',
}


class Slug:
    def __init__(self, phrase: str):
        self.phrase = self.clean_phrase(phrase)
        self.slug = self.generate_slug()

    def generate_slug(self):
        return ''.join(cyrillic_to_latin.get(letter, letter) for letter in self.phrase)

    @staticmethod
    def clean_phrase(phrase: str) -> str:
        if phrase and isinstance(phrase, str):
            phrase = phrase.lower().strip()
            return re.sub(r"-{2,}| +", '-', re.sub(r"[^\w\s-]", "", phrase))
        raise TypeError('The phrase must be a string!')


def get_sep(form):
    if not form.cleaned_data.get('custom_sep'):
        return form.cleaned_data.get('sep_choice')

    return form.cleaned_data.get('custom_sep')


def get_existing_originals(db_words) -> set[str]:
    return set(pair.original for pair in db_words)


def get_unique_pairs(text: str, existing_originals: set[str], sep, dictionary, PairWord):
    unique_pairs = []
    for pair in text.split('\n'):
        try:
            original, translation = pair.lower().strip().split(sep)
            if original not in existing_originals:
                unique_pairs.append(PairWord(original=original, translation=translation, dictionary=dictionary))
        except ValueError:
            unique_pairs.append(PairWord(original=pair.lower().strip(), translation='', dictionary=dictionary))
    return unique_pairs


def get_delete_and_updated_words(formset, PairWord, dictionary):
    words_to_delete = []
    updated_words = []

    for cleaned_data in formset.cleaned_data:
        delete_word = cleaned_data.get('delete')
        new_original = cleaned_data.get('original')
        new_translation = cleaned_data.get('translation')
        old_original = cleaned_data.get('id').original
        old_translation = cleaned_data.get('id').translation

        if delete_word:
            words_to_delete.append(cleaned_data.get('id').id)

        elif delete_word is False and (new_original != old_original or new_translation != old_translation):

            updated_word = PairWord(
                id=cleaned_data.get('id').id,
                original=cleaned_data.get('original'),
                translation=cleaned_data.get('translation'),
                dictionary=dictionary
            )
            updated_words.append(updated_word)

    return words_to_delete, updated_words


# Функции для представления StudyWordsView
def get_data_session(request, **kwargs):
    """
    Получает данные из сессии на основе переданных ключей.

    Args:
        request (HttpRequest): Запрос от клиента.
        **kwargs (dict): Словарь, содержащий ключи и значения по умолчанию для данных,
                      которые нужно получить из сессии.

    Returns:
        dict: Словарь, содержащий данные из сессии на основе переданных ключей.
              Если данные отсутствуют в сессии, используются значения по умолчанию из kwargs.

    Example:
        data = get_data_session(request,
                {'start_index': None, 'end_index': None, 'level': None, 'current_word_index': None, 'study_words': []})
        start_index = data['start_index']
        end_index = data['end_index']
        level = data['level']
        current_word_index = data['current_word_index']
        study_words = data['study_words']
    """
    data_session = {}
    for key, value in kwargs.items():
        data_session[key] = request.session.get(key, value)

    return data_session


def set_data_session(request, **kwargs):
    """
    Устанавливает значения в сессию на основе переданных ключей и их значений.

    Args:
        request (HttpRequest): Запрос от клиента.
        **kwargs: Пары ключ-значение для установки в сессию.

    Example:
        set_data_session(request, start_index=0, end_index=5, level=1, current_word_index=0, study_words=[])
    """
    for key, value in kwargs.items():
        request.session[key] = value


def study_process(request, **kwargs):
    """
    Обрабатывает процесс обучения пользователя словам из словаря.

    Args:
        request (HttpRequest): Запрос от клиента.
        **kwargs: Дополнительные параметры и объекты, необходимые для выполнения функции.

            Следующие константы и объекты должны быть переданы в kwargs:

            - STOP_LEARNING (int): Уровень, на котором обучение завершается.
            - NEXT_LEVEL_POINT (int): Количество баллов для перехода на следующий уровень.
            - START_INDEX: Индекс начала текущего среза слов. (Значение по умолчанию)
            - END_INDEX: Индекс конца текущего среза слов. (Значение по умолчанию)
            - STEP_INDEX (int): Шаг для увелечения end_index. (Значение по умолчанию)
            - POINT (int): Начальное количество балов. (Значение по умолчанию)
            - template_name (str): Имя шаблона, используемого для отображения страницы.
            - dict_slug (str): Слаг словаря, с которым работает пользователь.

            Дополнительные модели:

            - PairWord (model): Модель для работы с парами слов.
            - RepeatWordForm (form): Форма для ответа пользователя на слово.

            Следующие аргументы могут быть извлечены из данных сессии:

            - start_index (int): Индекс начала текущего среза слов.
            - end_index (int): Индекс конца текущего среза слов.
            - level (int): Текущий уровень обучения.
            - current_word_index (int): Индекс текущего изучаемого слова.
            - study_words (list): Список изучаемых слов с баллами.

    Returns:
        HttpResponse: HTTP-ответ с результатом обработки запроса.

    """

    data = get_data_session(request,
                            **{'start_index': kwargs['START_INDEX'],
                               'end_index': kwargs['END_INDEX'],
                               'level': 1,
                               'current_word_index': 0,
                               'study_words': []
                               })

    start_index = data.get('start_index', 1)
    end_index = data['end_index']
    level = request.session.get('level', 1)
    current_word_index = data['current_word_index']
    study_words = data['study_words']

    if level < kwargs['STOP_LEARNING']:
        if study_words:
            # проверяем количество балов у пар
            study_words = [{'pair': word['pair'], 'point': word['point']}
                           for word in study_words if word['point'] < kwargs['NEXT_LEVEL_POINT']]

        if not study_words:
            db_words = kwargs['PairWord'].objects.filter(dictionary__slug=kwargs['dict_slug']).order_by('id')
            # length_lst = abs(len(db_words) - end_index) if len(db_words) > 5 else len(db_words)
            # message = f'{length_lst} word{("", "s")[length_lst > 1]} left out of {len(db_words)}'
            # messages.info(request, message)

            if start_index > len(db_words) - 1:
                # если список слов закончился
                level += 1
                start_index, end_index = 0, 5

            study_words = [{'pair': (pair.original, pair.translation), 'point': 0}
                           for pair in db_words[start_index:end_index]]
            set_data_session(request, level=level, start_index=end_index,
                             end_index=end_index + kwargs['STEP_INDEX'])

        if current_word_index + 1 > len(study_words):
            current_word_index = 0

        set_data_session(request, study_words=study_words, current_word_index=current_word_index)

        title = ' '.join(kwargs["dict_slug"].split('-')).title()
        form = kwargs['RepeatWordForm']()
        reset_url = reverse('words:study_words', kwargs={'dict_slug': kwargs["dict_slug"]})

        context = {'translation': study_words[current_word_index]['pair'][1],
                   'title': f'Study {title}',
                   'form': form,
                   'slug': kwargs['dict_slug'],
                   'reset_url': reset_url,
                   'words_left': request.session.get('words_left')
                   }

        return render(request, kwargs['template_name'], context)
    else:
        data_reset = {
            'level': kwargs['LEVEL'],
            'original': None,
            'translation': None,
            'study_words': None,
            'start_index': kwargs['START_INDEX'],
            'end_index': kwargs['END_INDEX'],
            'step': kwargs['STEP_INDEX'],
            'point': kwargs['POINT'],
            'current_word_index': kwargs['CURRENT_WORD_INDEX']
        }
        set_data_session(request, **data_reset)
    return redirect(reverse('words:repeat_words', kwargs={'dict_slug': kwargs['dict_slug']}))

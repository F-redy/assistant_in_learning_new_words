import re

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


def get_unique_pairs(text: str, existing_originals: set[str], sep, id_dictionary: int, PairWord):
    unique_pairs = []
    for pair in text.split('\n'):
        try:
            original, translation = pair.split(sep)
            if original not in existing_originals:
                unique_pairs.append(PairWord(original=original, translation=translation, dictionary=id_dictionary))
        except ValueError:
            unique_pairs.append(PairWord(original=pair, translation='', dictionary=id_dictionary))
    return unique_pairs

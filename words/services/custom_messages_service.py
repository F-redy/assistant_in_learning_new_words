class CustomMessagesService:
    def __init__(self, request, current_word_index, words):
        self.request = request
        self.current_word_index = current_word_index
        self.words = words
        self.custom_messages = self.get_custom_messages()

    def __str__(self):
        return f'{self.get_custom_messages()}'

    def get_pair(self):
        if self.words:
            original, translation = self.words[self.current_word_index]['pair']
            point = self.words[self.current_word_index]['point']
            return original, translation, point
        return

    def check_user_answer(self):
        pair = self.get_pair()
        if pair:
            original, translation, point = pair
        else:
            raise ValueError('Empty list words')

        result = user_answer = point_message = None

        if self.request.POST:
            user_answer = self.request.POST.get('user_answer', '').strip().lower()

            if user_answer == original:
                result = True
                point += 1
                if point > 4:
                    point_message = 'pair goes to the next level'
                else:
                    point_message = f'point: {point}'
            else:
                result = False
                point -= 1
                point_message = f'point: {point}'

            self.words[self.current_word_index]['point'] = point

        self.request.session['study_words'] = self.words
        return result, original, translation, user_answer, point_message

    def get_custom_messages(self):
        result, original, translation, user_answer, point_message = self.check_user_answer()
        custom_messages = {}

        if not result:
            custom_messages['error_answer'] = True
            custom_messages['user_answer'] = user_answer

        custom_messages.update({
            'translation': translation,
            'original': original,
            'point': point_message,
        })

        return custom_messages

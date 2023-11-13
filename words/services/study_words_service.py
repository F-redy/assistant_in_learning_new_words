from random import shuffle

from words.models import PairWord, UserLearningData
from words.services.session_service import SessionService


class StudyWordsService:
    def __init__(self, request, active_session: SessionService):
        self.request = request
        self.active_session: UserLearningData = active_session.active_session
        self.study_words = self.get_study_words(self.request.session.get('study_words'))

    def handle_level_up(self, db_words):
        if self.active_session.start_index > len(db_words) - 1:
            self.active_session.level += 1
            self.active_session.start_index = 0
            self.active_session.end_index = self.active_session.step

    def filter_study_words(self, study_words):
        return [pair for pair in study_words if pair['point'] < self.active_session.next_level_point]

    def generate_study_words(self, db_words):
        study_words = [{'pair': [pair.original, pair.translation], 'point': self.active_session.point}
                       for pair in db_words[self.active_session.start_index:self.active_session.end_index]]

        self.active_session.current_word_index = 0
        self.active_session.start_index = self.active_session.end_index
        self.active_session.end_index += self.active_session.step

        shuffle(study_words)
        return study_words

    def get_study_words(self, study_words):
        if self.active_session.level > self.active_session.stop_learning:
            return

        if study_words:
            study_words = self.filter_study_words(study_words)
        if not study_words:
            db_words = PairWord.objects.filter(dictionary=self.active_session.dictionary).order_by('id')
            self.handle_level_up(db_words)
            study_words = self.generate_study_words(db_words)

        self.check_current_word_index(study_words)
        self.active_session.save()

        return study_words

    def check_current_word_index(self, study_words):
        if self.active_session.current_word_index + 1 > len(study_words):
            self.active_session.current_word_index = 0
            self.active_session.save()

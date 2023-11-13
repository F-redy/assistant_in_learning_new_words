from datetime import datetime

from words.models import Dictionary, UserLearningData


class SessionService:
    def __init__(self, request, dict_slug):
        self.request = request
        self.active_session: UserLearningData = self.get_or_create_active_session(dict_slug)
        self.reset_request_session()
        self.reset_data_active_session()

    def get_or_create_active_session(self, dict_slug: str):
        user = self.request.user
        dictionary = Dictionary.objects.filter(slug=dict_slug, user=user).first()
        active_session, _ = UserLearningData.objects.get_or_create(
            dictionary=dictionary, user=user
        )
        if not active_session.session_active:
            active_session.session_active = True

        active_session.save()
        return active_session

    def update_current_word_index(self, value: int = 1):
        self.active_session.current_word_index += value
        self.active_session.save()

    def reset_request_session(self):
        if self.active_session.dictionary.slug != self.request.session.get('dictionary_session'):
            self.request.session['study_words'] = None
            self.request.session['dictionary_session'] = '-'.join(self.active_session.dictionary.slug.split('_'))

    def reset_data_active_session(self, **kwargs):
        if self.check_days() or self.active_session.level > self.active_session.stop_learning:
            default_values = {
                'level': self.active_session._meta.get_field('level').get_default(),
                'start_index': self.active_session._meta.get_field('start_index').get_default(),
                'end_index': self.active_session._meta.get_field('end_index').get_default(),
                'step': self.active_session._meta.get_field('step').get_default(),
                'stop_learning': self.active_session._meta.get_field('stop_learning').get_default(),
                'point': self.active_session._meta.get_field('point').get_default(),
                'next_level_point': self.active_session._meta.get_field('next_level_point').get_default(),
                'current_word_index': self.active_session._meta.get_field('current_word_index').get_default(),
                'created_at': None,
                'session_active': self.active_session._meta.get_field('session_active').get_default()
            }

            default_values.update(kwargs)

            for field, value in default_values.items():
                setattr(self.active_session, field, value)

            self.active_session.save()

    def check_days(self):
        now = datetime.now()
        created_at = self.active_session.created_at

        match created_at:
            case str(created) if '+' not in created:
                created = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            case _:
                created = datetime.strptime(str(created_at)[:-6], '%Y-%m-%d %H:%M:%S')

        return (now - created).days

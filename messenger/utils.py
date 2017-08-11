import json

import logging

from django.conf import settings
from django.db.models import Case, When
from django.urls import reverse
from rest_framework.renderers import JSONRenderer

from api.serializers.manuscript import BaseManuscriptSerializer
from messenger.api import send_message
from messenger.api.formatters import format_text
from messenger.models import ChatSession
from quiz.models import AnswerSet, Answer, Manuscript, VoterGuideAlternative, VoterGuideAnswer


logger = logging.getLogger(__name__)


def render_and_load_manuscript(manuscript):
    return json.loads(JSONRenderer().render(BaseManuscriptSerializer(manuscript).data).decode())


def init_or_reset_session(sender_id, session=None, manuscript_pk=None):
    default_manuscript = Manuscript.objects.get_default()
    if manuscript_pk is None:
        manuscript = default_manuscript
    else:
        try:
            manuscript = Manuscript.objects.get(pk=manuscript_pk)
        except Manuscript.DoesNotExist:
            logger.warning("Session referenced non-existing manuscript={}".format(manuscript_pk))
            manuscript = default_manuscript

    if not default_manuscript:
        if settings.DEBUG:
            send_message(format_text(sender_id, "No manuscripts, bailing..."))

    # Serialize what we need and put in the session state
    meta = {
        'manuscript': render_and_load_manuscript(manuscript),
        'item': 0,
        'promise': 0,
        'first_name': ''
    }

    # Existing?
    if session is not None:
        session.meta = meta
        session.save()
        return session

    return ChatSession.objects.create(user_id=sender_id, meta=meta)


def _promises_as_dict(promise_list):
    return {str(p['pk']): p['status'] for p in promise_list}


def save_answers(chat_session: ChatSession):
    """ When all questions have been answered in a manuscript create answer objects. """
    answer_data = chat_session.meta.get('answers')
    if not answer_data:
        return

    if AnswerSet.objects.filter(session=chat_session).exists():
        return

    promises = _promises_as_dict(chat_session.meta['manuscript']['promises'])

    answer_set = AnswerSet.objects.create(session=chat_session)
    for promise_id, status in answer_data.items():
        Answer.objects.create(
            promise_id=promise_id,
            status=status,
            answer_set=answer_set,
            correct_status=promises[str(promise_id)] == status)


def delete_answers(session: ChatSession):
    AnswerSet.objects.filter(session=session).delete()


def save_vg_answer(session: ChatSession, payload):
    try:
        alt = VoterGuideAlternative.objects.get(pk=payload['alternative'])
    except VoterGuideAlternative.DoesNotExist:
        return
    answer_set, _ = AnswerSet.objects.get_or_create(session=session)  # reuse answerset
    answer, _ = VoterGuideAnswer.objects.get_or_create(answer_set=answer_set, voter_guide_alternative=alt)


def get_unanswered_vg_manuscripts(session: ChatSession, selection=None):
    ms = Manuscript.objects.filter(type=Manuscript.TYPE_VOTER_GUIDE)

    if selection:
        ms = ms.filter(pk__in=selection)

    answers = VoterGuideAnswer.objects.filter(answer_set__session=session)
    return ms.exclude(voter_guide_alternatives__answers__in=answers)


def get_next_vg_manuscript(session: ChatSession):
    ms = get_unanswered_vg_manuscripts(session)
    # TODO: Add skipped questions
    skipped = session.meta.get('skipped_manuscripts')

    current_category = session.meta['manuscript']['hdo_category']
    ms = ms.filter(hdo_category=current_category)
    if skipped:
        ms = ms.exclude(pk__in=skipped)

    return ms.first()


def get_voter_guide_manuscripts(session: ChatSession, selection=None):
    """ Get voter guide manuscripts that are not already answered, max 1 per HDO category """

    # Remove manuscripts already answered
    manuscripts = get_unanswered_vg_manuscripts(session, selection)

    # Make manuscripts unique per HDO category
    exclude_manuscripts = []
    seen_cats = []
    for m in manuscripts:
        if m.hdo_category.pk not in seen_cats:
            seen_cats.append(m.hdo_category.pk)
        else:
            exclude_manuscripts.append(m.pk)

    manuscripts = manuscripts.exclude(pk__in=exclude_manuscripts)

    # Random order
    order_by = '?'
    if selection:
        # Keep manuscript selection order
        order_by = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(selection)])

    manuscripts = manuscripts.order_by(order_by).select_related('hdo_category')
    return manuscripts


def get_result_url(session: ChatSession):
    url = reverse('quiz:answer-set-detail', args=[session.answers.uuid])
    return '{}{}'.format(settings.BASE_URL, url)


def get_messenger_bot_url():
    return 'https://m.me/{}'.format(settings.FACEBOOK_PAGE_ID)

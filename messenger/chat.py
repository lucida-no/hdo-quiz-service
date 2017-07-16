import logging
import random

from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext as _

from messenger.api import get_user_profile, send_message
from messenger.api.formatters import format_text, format_image_attachment

from messenger.intent_formatters import format_question, format_quick_reply_next
from messenger.intents import INTENT_ANSWER_QUIZ_QUESTION, INTENT_GET_HELP, INTENT_RESET_SESSION, INTENT_GET_STARTED
from messenger.models import ChatSession
from messenger.utils import save_answers

from quiz.models import ManuscriptItem

logger = logging.getLogger(__name__)


def get_replies(sender_id, session, payload=None):
    """ Look in session state and payload and format one or more replies to the user"""
    # TODO: Use intent namespace (ie. quiz. and general. vg. to route intents)
    # TODO: move quiz_1 and quiz_2 specific handlers to it's own file
    # TODO: Add voter_guide handlers (own file)
    # TODO: maybe this needs another abstraction level?
    replies = []
    manus = session.meta['manuscript']
    if session.meta['item'] >= len(manus['items']):
        return []

    item = manus['items'][session.meta['item']]

    if payload is not None:
        # User pressed a button or similiar
        intent = payload['intent']

        if intent in [INTENT_RESET_SESSION, INTENT_GET_STARTED]:
            # Just keep going
            pass
        elif intent == INTENT_GET_HELP:
            # FIXME: User is stuck
            return [format_text(sender_id, 'Ingen fare 😊 To setninger som forteller deg hvor du kan få hjelp ♿')]
        elif intent == INTENT_ANSWER_QUIZ_QUESTION:
            # Quiz: Answer replies
            replies += get_quiz_question_replies(sender_id, session, payload)

            # Update answer state
            current_answers = session.meta.get('answers', {})
            current_answers[payload['question']] = payload['answer']
            session.meta['answers'] = current_answers
        else:
            msg = "Error: Unknown intent '{}'".format(intent)
            send_message(format_text(sender_id, msg))
            raise Exception(msg)

    # Text items (add until no more)
    while item['type'] == ManuscriptItem.TYPE_TEXT and session.meta['item'] < len(manus['items']):
        logger.debug("Adding text reply: [{}]".format(session.meta['item'] + 1))

        replies += [format_text(sender_id, item['text'])]
        session.meta['item'] += 1
        if session.meta['item'] < len(manus['items']):
            # Last item in manuscript!
            item = manus['items'][session.meta['item']]

    # Quiz: Show checked promises question
    if item['type'] == ManuscriptItem.TYPE_Q_PROMISES_CHECKED:
        if session.meta['promise'] == len(manus['promises']):
            # Last promise in checked promises quiz
            logger.debug("Last promise: [{}]".format(session.meta['item'] + 1))

            session.meta['item'] += 1
            replies += get_replies(sender_id, session)  # Add next item reply
        else:
            logger.debug("Adding promise reply: [{}]".format(session.meta['promise'] + 1))

            question = manus['promises'][session.meta['promise']]
            question_text = 'Løfte #{} {}'.format(session.meta['promise'] + 1, question['body'])
            replies += [format_question(sender_id, question, question_text)]
            session.meta['promise'] += 1

    # Quick replies
    elif item['type'] == ManuscriptItem.TYPE_QUICK_REPLY:
        logger.debug("Adding quick reply: [{}]".format(session.meta['item'] + 1))

        replies += [format_quick_reply_next(sender_id, item['text'], item['reply_text_1'])]
        session.meta['item'] += 1

    # Quiz: Show results
    elif item['type'] == ManuscriptItem.TYPE_QUIZ_RESULT:
        logger.debug("Adding quiz result [{}]".format(session.meta['item'] + 1))

        replies += [format_text(sender_id, get_quiz_result_url(session))]
        session.meta['item'] += 1

    else:
        logger.warning("Unhandled manuscript item type: {} [{}]".format(item['type'], session.meta['item'] + 1))

    return replies


def get_quiz_result_url(session: ChatSession):
    url = reverse('quiz:answer-set-detail', args=[session.answers.uuid])
    return '{}{}'.format(settings.BASE_URL, url)


def get_quiz_question_replies(sender_id, session, payload):
    """ Get replies to quix answers INTENT_ANSWER_QUIZ_QUESTION """
    first_name = session.meta['first_name']
    if not first_name:
        first_name = session.meta['first_name'] = get_user_profile(sender_id)['first_name']

    # Get last asked promise
    p_i = session.meta['promise']
    if p_i > 0:
        p_i -= 1
    promise = session.meta['manuscript']['promises'][p_i]

    # Is answer correct?
    if payload['answer'] == promise['status']:
        text = 'Godt svar {} 🙂 Det løftet ble {}'.format(first_name, _(promise['status']))
    else:
        text = 'Beklager {} 😩  Det var ikke riktig, det løftet ble {}'.format(first_name, _(promise['status']))

    replies = [format_text(sender_id, text)]

    # Try to get a random image of correct type and display 1 out of 3 times
    images = list(filter(lambda x: x['type'] == promise['status'], session.meta['manuscript']['images']))
    if images and session.meta['promise'] % 3 == 0:
        image = random.choice(images)
        replies += [format_image_attachment(sender_id, image['url'])]

    # Is last promise?
    if session.meta['promise'] == len(session.meta['manuscript']['promises']):
        save_answers(session)

    return replies

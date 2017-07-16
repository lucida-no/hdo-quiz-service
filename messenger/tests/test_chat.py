from django.core.management import call_command

from messenger.handlers import received_event


def test_on_receive_messages(db):
    call_command('loaddata', 'testdata')
    incoming = {
        'sender': {
            'id': '1234'
        }
    }
    received_event(incoming)
